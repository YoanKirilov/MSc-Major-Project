import asyncio
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from app.explanations.cve import explain_cves
from app.explanations.service import GeneratedExplanationBatch
from app.main import create_app
from app.scanner.cve import NvdBusy, NvdClient, application_cpe, service_cpe
from app.scanner.parser import parse_host
from app.schemas.cve import CveLookup
from app.schemas.scan import ScanDocument, Service
from app.security.session import SessionManager
from app.storage.annotations import AnnotationStore
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client

CPE = "cpe:/a:apache:http_server:2.4.49"
QUERY = "cpe:2.3:a:apache:http_server:2.4.49:*:*:*:*:*:*:*"


def software(**changes):
    return Service(
        **{
            "service_id": str(uuid4()),
            "device_id": str(uuid4()),
            "port": 443,
            "state": "open",
            "detection_method": "probed",
            "nmap_confidence": 10,
            "cpes": [CPE],
            **changes,
        }
    )


def nvd_data():
    return {
        "totalResults": 1,
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2021-41773",
                    "vulnStatus": "Analyzed",
                    "descriptions": [
                        {"lang": "en", "value": "Synthetic description, not live evidence."}
                    ],
                }
            }
        ],
    }


@pytest.mark.parametrize(
    "value",
    [
        "cpe:/a:apache:http_server",
        "cpe:/a:apache:http_server:*",
        "cpe:/o:linux:kernel:1.0",
        "cpe:/a:apache:http_server:2.4%3a49",
        "cpe:/a:apache:http_server:~packed",
        "https://example.com",
        "cpe:/a:apache:http_server:latest",
    ],
)
def test_imprecise_or_unsupported_cpes_are_not_guessed(value):
    assert application_cpe(value) is None


def test_cpe_version_is_preserved_and_port_does_not_select_cve():
    assert application_cpe(CPE) == QUERY
    assert application_cpe(QUERY) == QUERY
    for changes in (
        {"cpes": []},
        {"state": "filtered"},
        {"detection_method": "table"},
        {"nmap_confidence": 6},
        {"cpes": [CPE, CPE.replace("49", "48")]},
    ):
        assert service_cpe(software(**changes)) is None


def test_parser_saves_service_cpes_and_old_reports_default_to_empty():
    xml = (Path(__file__).parents[1] / "fixtures/nmap_host.xml").read_bytes()
    xml = xml.replace(
        b'<service name="telnet" method="probed" conf="9" />',
        f'<service name="http" method="probed" conf="9"><cpe>{CPE}</cpe></service>'.encode(),
    )
    _, services = parse_host(xml, "192.168.56.10", "test")
    assert next(s for s in services if s.port == 23).cpes == [CPE]
    assert Service(service_id="old", device_id="old", port=80).cpes == []


@pytest.mark.asyncio
async def test_nvd_uses_only_specific_cpe_and_enforces_pause():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.host == "services.nvd.nist.gov"
        assert request.url.params["cpeName"] == QUERY
        assert "isVulnerable" in request.url.params
        assert set(request.url.params) == {
            "cpeName",
            "isVulnerable",
            "noRejected",
            "resultsPerPage",
        }
        return httpx.Response(200, json=nvd_data())

    client = NvdClient(httpx.MockTransport(handler))
    result = await client.lookup(software())
    assert result.results[0].cve_id == "CVE-2021-41773"
    assert result.status == "candidates"
    with pytest.raises(NvdBusy):
        await client.lookup(software())
    insufficient = await client.lookup(software(cpes=[]))
    assert insufficient.status == "insufficient_evidence"
    assert len(calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response,expected",
    [
        (httpx.Response(200, json={"totalResults": 0, "vulnerabilities": []}), "no_matches"),
        (httpx.Response(429), "unavailable"),
        (httpx.Response(302, headers={"location": "http://127.0.0.1"}), "unavailable"),
        (httpx.Response(200, json={"totalResults": 1, "vulnerabilities": []}), "unavailable"),
        (httpx.Response(200, content=b"x" * 1_000_001), "unavailable"),
    ],
)
async def test_no_matches_is_distinct_from_failed_lookup(response, expected):
    def handler(request):
        if "/cpes/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "totalResults": 1,
                    "products": [{"cpe": {"cpeName": QUERY, "deprecated": False}}],
                },
            )
        return response

    client = NvdClient(httpx.MockTransport(handler))
    client.request_interval_s = 0
    result = await client.lookup(software())
    assert result.status == expected


class CveProvider:
    name = "ollama"
    model = "synthetic"

    def __init__(self, invent=False):
        self.invent = invent
        self.inputs = []

    async def generate(self, findings):
        self.inputs = findings
        choices = findings[0]["reviewed_choices"]
        output = {
            key: [part[-1] for part in value] if isinstance(value[0], list) else value[-1]
            for key, value in choices.items()
        }
        if self.invent:
            output["meaning"] = "This device is vulnerable to CVE-9999-12345."
        return GeneratedExplanationBatch.model_validate(
            {"explanations": [{"finding_id": "cve-context", **output}]}
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("invent", [False, True])
async def test_ai_can_explain_context_but_cannot_invent_matches(invent):
    lookup = CveLookup(
        service_id="private-id",
        checked_at="2026-10-02T00:00:00Z",
        status="candidates",
        message="Possible matches, not confirmed flaws.",
    )
    provider = CveProvider(invent)
    result = await explain_cves(lookup, provider)
    assert result.ai_source == ("fixed" if invent else "ollama")
    assert "private-id" not in str(provider.inputs)
    assert "CVE-9999" not in str(result.model_dump())


@pytest.mark.parametrize("initial_ai_failure", [False, True])
def test_authenticated_cve_lookup_saves_annotations_and_cache_without_rewriting_scan(
    initial_ai_failure,
):
    manager = SessionManager()
    app = create_app(session_manager=manager)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=nvd_data())

    with TestClient(app, base_url=BASE_URL) as client:
        service = software()
        scan = ScanDocument(
            scan_id=str(uuid4()),
            phase="finished",
            state="completed",
            target={"mode": "known_hosts", "hosts": ["192.168.0.10"]},
            services=[service],
        )
        app.state.store._create_scan(scan)
        primary = app.state.store._scan_dir(scan.scan_id) / "scan.json"
        original = primary.read_bytes()
        app.state.nvd = NvdClient(httpx.MockTransport(handler))
        app.state.explanations.provider = CveProvider(invent=initial_ai_failure)
        path = f"/api/live-scans/{scan.scan_id}/services/{service.service_id}/cves"
        assert client.post(path, json={}).status_code in {401, 403}
        headers = authenticate_client(client, manager)
        # Pre-resolution empty results must not hide the new dictionary lookup for 24h.
        from app.schemas.common import iso_z, utc_now

        AnnotationStore(app.state.store)._update(
            scan.scan_id,
            cve=CveLookup(
                service_id=service.service_id,
                query=QUERY,
                checked_at=iso_z(utc_now()),
                status="no_matches",
                message="Old exact-only lookup.",
            ),
        )
        response = client.post(path, headers=headers, json={})
        assert response.status_code == 200, response.text
        assert response.json()["annotations"]["revision"] == response.json()["revision"]
        renamed = client.put(
            f"/api/live-scans/{scan.scan_id}/title",
            headers=headers,
            json={
                "title": "Changed in another tab",
                "expected_revision": response.json()["revision"],
            },
        )
        assert renamed.status_code == 200
        assert response.json()["lookup"]["ai_source"] == (
            "fixed" if initial_ai_failure else "ollama"
        )
        app.state.explanations.provider = CveProvider()
        retried = client.post(path, headers=headers, json={}).json()
        assert retried["cached"]
        assert retried["annotations"]["title"] == "Changed in another tab"
        assert retried["annotations"]["revision"] == retried["revision"]
        assert retried["lookup"]["ai_source"] == "ollama"
        assert retried["lookup"]["ai_fallback_reason"] is None
        assert len(calls) == 1
        assert primary.read_bytes() == original
        saved = AnnotationStore(app.state.store)._load(scan.scan_id)
        assert saved.cve_lookups[0].results[0].cve_id == "CVE-2021-41773"
        assert (
            client.post(
                path.replace(service.service_id, str(uuid4())), headers=headers, json={}
            ).status_code
            == 404
        )


def test_report_cve_availability_uses_lookup_policy_without_changing_saved_facts():
    manager = SessionManager()
    app = create_app(session_manager=manager)
    services = [
        software(),
        software(cpes=["cpe:/a:igor_sysoev:nginx"]),
        software(cpes=["cpe:/o:linux:linux_kernel:5.0"]),
        software(cpes=[CPE, CPE.replace("49", "48")]),
        software(cpes=[]),
        software(nmap_confidence=6),
        software(state="filtered"),
    ]
    with TestClient(app, base_url=BASE_URL) as client:
        scan = ScanDocument(
            scan_id=str(uuid4()),
            phase="finished",
            state="completed",
            target={"mode": "known_hosts", "hosts": ["192.168.0.10"]},
            services=services,
        )
        app.state.store._create_scan(scan)
        path = app.state.store._scan_dir(scan.scan_id) / "scan.json"
        original = path.read_bytes()
        authenticate_client(client, manager)
        response = client.get(f"/api/live-scans/{scan.scan_id}")
        assert response.status_code == 200
        for saved, shown in zip(services, response.json()["services"], strict=True):
            assert shown["cve_lookup_available"] is (service_cpe(saved) is not None)
        assert response.json()["services"][0]["cve_lookup_available"]
        assert not any(s["cve_lookup_available"] for s in response.json()["services"][1:])
        assert path.read_bytes() == original


@pytest.mark.asyncio
async def test_provider_timeout_preserves_references(monkeypatch):
    import app.explanations.cve as module

    original_timeout = asyncio.timeout
    monkeypatch.setattr(module.asyncio, "timeout", lambda _: original_timeout(0.01))

    class Slow(CveProvider):
        async def generate(self, findings):
            await asyncio.sleep(1)

    lookup = CveLookup(service_id="x", checked_at="now", status="no_matches", message="No matches.")
    result = await explain_cves(lookup, Slow())
    assert result.ai_source == "fixed"
    assert result.status == "no_matches"
    assert result.explanation
