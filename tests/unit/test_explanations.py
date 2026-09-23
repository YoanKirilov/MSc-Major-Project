import json
from uuid import uuid4

import httpx
import pytest

from app.explanations.service import (
    ExplanationService,
    GeneratedExplanation,
    GeneratedExplanationBatch,
    OllamaExplanationProvider,
    build_safe_findings,
)
from app.schemas.scan import Device, Finding, ScanDocument, Service
from app.schemas.settings import SettingsUpdate
from app.storage.json_store import JsonStore
from app.risk.engine import evaluate_device
from tests.fixtures.fixtures import make_telnet_scan


async def make_stored_scan(tmp_path):
    fixture = make_telnet_scan()
    document = ScanDocument(
        scan_id="2d9aaddd-4c59-41dd-b5d8-256e5b49c811",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.0.10"]},
        devices=[Device.model_validate(fixture["device"])],
        services=[Service.model_validate(fixture["service"])],
        findings=[Finding.model_validate(fixture["finding"])],
    )
    document.findings = evaluate_device(document.devices[0], document.services)
    store = JsonStore(tmp_path)
    await store.create_scan(document)
    await store.update_settings(SettingsUpdate(expected_revision=1, ai_enabled=True), 1)
    return store, document


class FakeProvider:
    name = "ollama"
    model = "test-model"

    def __init__(self):
        self.calls = []

    async def generate(self, findings):
        self.calls.append(findings)
        return GeneratedExplanationBatch(
            explanations=[
                GeneratedExplanation(
                    finding_id=item["finding_id"],
                    title=item["verified_title"],
                    meaning=item["reviewed_choices"]["meaning"][-1],
                    why_it_matters=item["reviewed_choices"]["why_it_matters"][-1],
                    limitations=item["verified_limitations"],
                    recommended_steps=item["verified_recommended_steps"],
                    how_to_check=item["verified_how_to_check"],
                )
                for item in findings
            ]
        )


@pytest.mark.asyncio
async def test_explanation_service_persists_and_reuses_valid_ai_wording(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    provider = FakeProvider()
    service = ExplanationService(store, provider, enabled=True)

    await service.explain_scan(document.scan_id)
    await service.explain_scan(document.scan_id)

    saved = await store.load_scan(document.scan_id)
    assert provider.calls and len(provider.calls) == 1
    assert saved.ai_requests_used == 1
    assert saved.explanations[0].status == "ready"
    assert saved.explanations[0].source == "ai"
    assert saved.explanations[0].content.meaning.startswith("This device")
    assert saved.explanations[0].content.recommended_steps == [
        action.text for action in document.findings[0].actions
    ]


@pytest.mark.asyncio
async def test_explanation_service_uses_fixed_fallback_when_provider_fails(tmp_path):
    store, document = await make_stored_scan(tmp_path)

    class FailingProvider(FakeProvider):
        async def generate(self, findings):
            raise httpx.ConnectError("offline")

    await ExplanationService(store, FailingProvider(), enabled=True).explain_scan(document.scan_id)

    saved = await store.load_scan(document.scan_id)
    record = saved.explanations[0]
    assert record.status == "fallback"
    assert record.source == "fixed"
    assert record.fallback_reason == "provider_unavailable"
    assert record.content == saved.findings[0].fixed_explanation


@pytest.mark.asyncio
async def test_explanation_service_rejects_new_security_concepts(tmp_path):
    store, document = await make_stored_scan(tmp_path)

    class EmbellishingProvider(FakeProvider):
        async def generate(self, findings):
            return GeneratedExplanationBatch(
                explanations=[
                    GeneratedExplanation(
                        finding_id=findings[0]["finding_id"],
                        title=findings[0]["verified_title"],
                        meaning="This service may reveal a password.",
                        why_it_matters="The verified explanation did not make that claim.",
                        limitations=findings[0]["verified_limitations"],
                        recommended_steps=findings[0]["verified_recommended_steps"],
                        how_to_check=findings[0]["verified_how_to_check"],
                    )
                ]
            )

    await ExplanationService(store, EmbellishingProvider(), enabled=True).explain_scan(
        document.scan_id
    )

    saved = await store.load_scan(document.scan_id)
    record = saved.explanations[0]
    assert record.status == "fallback"
    assert record.fallback_reason == "invalid_provider_response"
    assert record.content == document.findings[0].fixed_explanation


@pytest.mark.asyncio
async def test_one_bad_rewrite_does_not_discard_other_valid_explanations(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    second = document.findings[0].model_copy(deep=True)
    second.finding_id = "e1fc3e42-d632-4999-b307-e69395734f9b"
    await store.update_scan(
        document.scan_id,
        lambda current: current.model_copy(update={"findings": [*current.findings, second]}),
    )

    class MixedProvider(FakeProvider):
        async def generate(self, findings):
            return GeneratedExplanationBatch(explanations=[
                GeneratedExplanation(
                    finding_id=findings[0]["finding_id"],
                    title=findings[0]["verified_title"],
                    meaning=findings[0]["reviewed_choices"]["meaning"][-1],
                    why_it_matters=findings[0]["reviewed_choices"]["why_it_matters"][-1],
                    limitations=findings[0]["verified_limitations"],
                    recommended_steps=findings[0]["verified_recommended_steps"],
                    how_to_check=findings[0]["verified_how_to_check"],
                ),
                GeneratedExplanation(
                    finding_id=findings[1]["finding_id"],
                    title=findings[1]["verified_title"],
                    meaning="This service may reveal a password.",
                    why_it_matters="The verified explanation did not make that claim.",
                    limitations=findings[1]["verified_limitations"],
                    recommended_steps=findings[1]["verified_recommended_steps"],
                    how_to_check=findings[1]["verified_how_to_check"],
                ),
            ])

    await ExplanationService(store, MixedProvider(), enabled=True).explain_scan(document.scan_id)
    saved = await store.load_scan(document.scan_id)
    assert [record.status for record in saved.explanations] == ["ready", "fallback"]
    assert saved.explanations[1].content == second.fixed_explanation


@pytest.mark.asyncio
async def test_ai_can_simplify_titles_limitations_and_steps_without_changing_rules(tmp_path):
    store, document = await make_stored_scan(tmp_path)

    class MoreGuidanceProvider(FakeProvider):
        async def generate(self, findings):
            return GeneratedExplanationBatch(explanations=[GeneratedExplanation(
                finding_id=findings[0]["finding_id"],
                title="Older remote control found (Telnet)",
                meaning=findings[0]["verified_meaning"],
                why_it_matters=findings[0]["verified_why_it_matters"],
                limitations=[
                    "Only the selected checks on your local network were used.",
                    "The scan did not try any sign-in details or attempt to sign in.",
                ],
                recommended_steps=[
                    "Check the settings or manual to find out whether this device needs Telnet.",
                    "If you need remote control, look for a protected option recommended by the device maker.",
                ],
                how_to_check=[
                    "If you do not use it, ask the owner or device maker how to turn it off safely.",
                    "Check that the new option works before turning off the old one.",
                ],
            )])

    await ExplanationService(store, MoreGuidanceProvider(), enabled=True).explain_scan(document.scan_id)
    saved = await store.load_scan(document.scan_id)
    record = saved.explanations[0]
    assert record.status == "ready"
    assert set(record.ai_fields) >= {"title", "limitations", "recommended_steps", "how_to_check"}
    assert record.display_title == "Older remote control found (Telnet)"
    assert record.display_limitations[0] == "Only the selected checks on your local network were used."
    assert "settings or manual" in record.content.recommended_steps[0]
    assert saved.findings == document.findings


@pytest.mark.asyncio
async def test_ai_batches_larger_reports_and_caps_optional_work(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    copies = []
    for _ in range(25):
        copy = document.findings[0].model_copy(deep=True)
        copy.finding_id = str(uuid4())
        copies.append(copy)
    await store.update_scan(
        document.scan_id,
        lambda current: current.model_copy(update={"findings": copies}),
    )
    provider = FakeProvider()
    await ExplanationService(store, provider, enabled=True).explain_scan(document.scan_id)
    saved = await store.load_scan(document.scan_id)
    assert len(provider.calls) == 4
    assert all(len(call) <= 6 for call in provider.calls)
    assert saved.ai_requests_used == 4
    assert sum(record.status == "ready" for record in saved.explanations) == 24
    assert saved.explanations[-1].fallback_reason == "ai_limit_reached"


@pytest.mark.asyncio
async def test_ai_never_exceeds_saved_report_request_limit(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    await store.update_scan(document.scan_id, lambda current: current.model_copy(update={
        "ai_requests_used": 12,
    }))
    provider = FakeProvider()
    await ExplanationService(store, provider, enabled=True).explain_scan(document.scan_id)
    saved = await store.load_scan(document.scan_id)
    assert provider.calls == []
    assert saved.ai_requests_used == 12
    assert saved.explanations[0].fallback_reason == "ai_request_limit"


@pytest.mark.asyncio
async def test_disabled_explanation_service_does_not_call_provider(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    provider = FakeProvider()

    await ExplanationService(store, provider, enabled=False).explain_scan(document.scan_id)

    saved = await store.load_scan(document.scan_id)
    assert provider.calls == []
    assert saved.explanations == []
    assert saved.ai_requests_used == 0


@pytest.mark.asyncio
async def test_saved_user_setting_controls_ai_even_when_provider_is_enabled(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    await store.update_settings(SettingsUpdate(expected_revision=2, ai_enabled=False), 2)
    provider = FakeProvider()
    await ExplanationService(store, provider, enabled=True).explain_scan(document.scan_id)
    saved = await store.load_scan(document.scan_id)
    assert provider.calls == []
    assert saved.ai_requests_used == 0


def test_ai_rewrite_cannot_remove_a_source_qualifier():
    with pytest.raises(ValueError, match="qualifier_removed"):
        ExplanationService._validated_line(
            "Management information may not be protected.",
            "Management information is visible.",
            field="why_it_matters",
            rule_id="R01",
        )


def test_ai_rewrite_cannot_drop_untested_scan_limitation():
    with pytest.raises(ValueError, match="scan_limitation_removed"):
        ExplanationService._validated_line(
            "Telnet normally sends information without encryption. This scan did not check sign-in.",
            "Telnet normally sends information without encryption.",
            field="why_it_matters",
            rule_id="R01",
        )


def test_ai_rewrite_must_keep_the_untested_subject():
    with pytest.raises(ValueError, match="scan_limitation_changed"):
        ExplanationService._validated_line(
            "This scan did not try to sign in or check who can use it.",
            "This scan did not check whether the device can work.",
            field="why_it_matters",
            rule_id="R01",
        )


def test_ai_step_cannot_add_a_new_device_change():
    with pytest.raises(ValueError, match="new_action"):
        ExplanationService._validated_line(
            "Check whether this service is needed.",
            "Turn it off immediately.",
            field="recommended_steps",
            rule_id="R01",
        )


def test_ai_step_must_keep_ask_owner_precaution():
    with pytest.raises(ValueError, match="action_precaution_removed"):
        ExplanationService._validated_line(
            "If you do not use it, ask the owner how to turn it off safely.",
            "If you do not use it, check how to turn it off safely.",
            field="how_to_check",
            rule_id="R01",
        )


@pytest.mark.asyncio
async def test_ollama_provider_requests_schema_constrained_local_output():
    async def handler(request):
        body = json.loads(request.content)
        assert request.url.host == "127.0.0.1"
        assert body["stream"] is False
        assert body["format"]["type"] == "object"
        response_content = json.dumps({
            "explanations": [{
                "finding_id": "finding-1",
                "title": "Service found",
                "meaning": "A service that needs checking was found.",
                "why_it_matters": "It may be available to other devices in your home.",
                "limitations": [],
                "recommended_steps": [],
                "how_to_check": [],
            }]
        })
        return httpx.Response(200, json={"message": {"content": response_content}})

    provider = OllamaExplanationProvider(
        model="test-model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.generate([{"finding_id": "finding-1"}])

    assert result.explanations[0].finding_id == "finding-1"


def test_ai_payload_excludes_network_identifiers_and_remote_ollama_urls(tmp_path):
    fixture = make_telnet_scan()
    document = ScanDocument(
        scan_id="2d9aaddd-4c59-41dd-b5d8-256e5b49c811",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.0.10"]},
        devices=[Device.model_validate(fixture["device"])],
        services=[Service.model_validate(fixture["service"])],
        findings=[Finding.model_validate(fixture["finding"])],
    )

    payload = json.dumps(build_safe_findings(document))
    assert "192.168.0.10" not in payload
    assert document.devices[0].device_id not in payload
    assert document.services[0].service_id not in payload
    with pytest.raises(ValueError, match="loopback"):
        OllamaExplanationProvider(model="test-model", base_url="http://example.com:11434")


def test_generated_explanation_rejects_unsupported_absolute_claims():
    with pytest.raises(ValueError, match="unsupported_absolute_claim"):
        ExplanationService._validated_line(
            "Traffic may not be protected.",
            "Anyone can read everything sent by this device.",
            field="why_it_matters",
            rule_id="R01",
        )


@pytest.mark.parametrize("source,candidate,field", [
    (
        "This device offers an FTP service for moving files across your local network.",
        "FTP is a file-sharing service that sends file contents or sign-in details without encryption.",
        "meaning",
    ),
    (
        "This device offers a web page over HTTP on your local network.",
        "This device does not offer a web page over HTTP on your local network.",
        "meaning",
    ),
    (
        "If you need remote control, look for a protected option recommended by the manufacturer.",
        "If you need remote control, use a connection without protection.",
        "recommended_steps",
    ),
    (
        "Review the sharing settings with the device's owner.",
        "Limit shared-folder access to people who need it.",
        "how_to_check",
    ),
    (
        "Check whether this connection is expected for the device.",
        "Check if this connection is expected for the device.",
        "recommended_steps",
    ),
])
def test_unreviewed_or_cosmetic_changes_cannot_be_labelled_simpler(source, candidate, field):
    with pytest.raises(ValueError):
        ExplanationService._validated_line(source, candidate, field=field, rule_id="R02")


@pytest.mark.asyncio
async def test_live_review_ftp_regression_keeps_original_claim(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    service = document.services[0].model_copy(update={"name": "ftp", "port": 21})
    finding = evaluate_device(document.devices[0], [service])[0]
    await store.update_scan(document.scan_id, lambda current: current.model_copy(update={
        "services": [service], "findings": [finding],
    }))

    class DriftingProvider(FakeProvider):
        async def generate(self, findings):
            return GeneratedExplanationBatch(explanations=[GeneratedExplanation(
                finding_id=finding.finding_id,
                title="File transfer found (FTP)",
                meaning="FTP is a file-sharing service that sends file contents or sign-in details without encryption.",
                why_it_matters=finding.fixed_explanation.why_it_matters,
            )])

    result = await ExplanationService(store, DriftingProvider(), enabled=True).explain_scan(document.scan_id)
    assert result.explanations[0].content.meaning == finding.fixed_explanation.meaning
    assert result.explanations[0].ai_fields == ["title"]
    assert result.findings == [finding]
