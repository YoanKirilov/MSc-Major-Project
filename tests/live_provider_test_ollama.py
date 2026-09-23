import os

import pytest

from app.explanations import ExplanationService, OllamaExplanationProvider
from app.schemas.scan import Device, Finding, ScanDocument, Service
from app.schemas.settings import SettingsUpdate
from app.storage.json_store import JsonStore
from app.risk.engine import evaluate_device
from app.explanations.wording import wording_choices
from tests.fixtures.fixtures import make_telnet_scan


@pytest.mark.live_provider
@pytest.mark.skipif(
    os.getenv("RUN_LIVE_OLLAMA") != "1",
    reason="Set RUN_LIVE_OLLAMA=1 to call the explicitly configured local Ollama service.",
)
@pytest.mark.asyncio
async def test_local_ollama_explanation_is_validated_and_persisted(tmp_path):
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
    provider = OllamaExplanationProvider(model="llama3.2:3b", timeout_s=120)

    await ExplanationService(store, provider, enabled=True).explain_scan(document.scan_id)

    saved = await store.load_scan(document.scan_id)
    assert saved.ai_requests_used == 1
    assert saved.explanations[0].status in {"ready", "fallback"}
    if saved.explanations[0].status == "ready":
        assert saved.explanations[0].source == "ai"
    else:
        assert saved.explanations[0].source == "fixed"
        assert saved.explanations[0].fallback_reason in {"invalid_provider_response", "not_simpler"}
    assert saved.explanations[0].content
    assert saved.findings[0].severity == "high"
    assert saved.findings[0].actions == document.findings[0].actions
    record = saved.explanations[0]
    original = document.findings[0]
    assert record.content.meaning in wording_choices(original.fixed_explanation.meaning)
    assert record.content.why_it_matters in wording_choices(original.fixed_explanation.why_it_matters)
    for action, step, check in zip(original.actions, record.content.recommended_steps, record.content.how_to_check, strict=True):
        assert step in wording_choices(action.text)
        assert check in wording_choices(action.verification)
