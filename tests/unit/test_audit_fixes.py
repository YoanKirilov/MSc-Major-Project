import asyncio
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from app.config import AppConfig, detect_private_network, network_warning, resolve_allowed_network
from app.explanations.service import ExplanationService
from app.jobs.supervisor import ScanSupervisor
from app.main import create_app
from app.scanner.names import add_name
from app.scanner.parser import parse_discovery_details
from app.scanner.pihole import PiholeClient
from app.scanner.runner import ProcessResult
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from fastapi.testclient import TestClient
from tests.fixtures.provider import ReviewedProvider
from tests.session_helpers import BASE_URL, authenticate_client
from tests.unit.test_explanations import make_stored_scan


def test_larger_default_network_does_not_select_virtual_adapter(monkeypatch):
    monkeypatch.setattr("app.config.os", SimpleNamespace(name="nt"))
    output = """
VMware:
   IPv4 Address: 192.168.91.1
   Subnet Mask: 255.255.255.0

WiFi:
   IPv4 Address: 10.240.108.40
   Subnet Mask: 255.255.252.0
   Default Gateway: 10.240.108.1
"""
    monkeypatch.setattr(
        "app.config.subprocess.run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=output)
    )
    assert detect_private_network() == "10.240.108.0/22"
    assert resolve_allowed_network(AppConfig()) is None
    assert network_warning("192.168.0.0/24", detect_private_network())
    assert network_warning("10.240.108.0/24", detect_private_network()) is None
    monkeypatch.setattr(
        "app.config.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=output.split("WiFi:")[0]),
    )
    assert detect_private_network() is None


def test_linux_detection_uses_default_route_not_first_private_adapter(monkeypatch):
    monkeypatch.setattr("app.config.os", SimpleNamespace(name="posix"))

    def run(args, **kwargs):
        output = (
            "2: virbr0 inet 192.168.91.1/24\n3: wlan0 inet 10.240.108.40/22\n"
            if "addr" in args
            else "default via 10.240.108.1 dev wlan0 proto dhcp\n"
        )
        return SimpleNamespace(returncode=0, stdout=output)

    monkeypatch.setattr("app.config.subprocess.run", run)
    assert detect_private_network() == "10.240.108.0/22"
    assert network_warning("invalid-range", detect_private_network())


def test_network_mismatch_rejected_before_job_is_created(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.0.0/24")
    monkeypatch.setattr("app.api.scans.detect_private_network", lambda: "10.240.108.0/22")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "test"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "test-nmap")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post(
            "/api/live-scans",
            headers=headers,
            json={"mode": "discover", "authorised": True},
        )
        assert response.status_code == 409
        assert "differs from the active network" in response.json()["detail"]
    assert not list((tmp_path / "app-data" / "scans").glob("*/scan.json"))


def test_progress_requires_session_and_returns_small_payload():
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        document = ScanDocument(
            scan_id=str(uuid4()),
            source="live",
            target={"mode": "known_hosts", "hosts": ["192.168.0.2"]},
        )
        client.app.state.store._create_scan(document)
        url = f"/api/live-scans/{document.scan_id}/progress"
        assert client.get(url).status_code == 401
        authenticate_client(client, manager)
        response = client.get(url)
        assert response.status_code == 200
        assert response.json()["target"] == {"mode": "known_hosts"}
        assert "services" not in response.json()


@pytest.mark.asyncio
async def test_full_report_can_finish_without_replacing_evidence(tmp_path):
    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "demo", "hosts": []},
        state="running",
        phase="analysis",
        scan_outcome="completed",
        analysis_status="running",
    )
    await store.create_scan(doc)
    primary = tmp_path / "scans" / doc.scan_id / "scan.json"
    before = primary.read_bytes()
    store.max_document_bytes = len(before)
    await ScanSupervisor(store)._finish_explanations(
        doc.scan_id, warning_code="AI_EXPLANATION_FAILED"
    )
    assert primary.read_bytes() == before
    final = await store.load_scan(doc.scan_id)
    assert final.state == "completed" and final.phase == "finished"
    assert final.analysis_status == "failed"
    assert (await store.load_progress(doc.scan_id))["phase"] == "finished"
    assert not await store.list_incomplete_scan_ids()
    assert (await store.list_scans(source=None, offset=0, limit=20))["items"][0][
        "state"
    ] == "completed"
    await store.finish_scan(
        doc.scan_id,
        lambda current: current.model_copy(update={"analysis_error": "retry unavailable"}),
    )
    repeated = await store.load_scan(doc.scan_id)
    assert repeated.state == "completed" and repeated.phase == "finished"
    assert repeated.analysis_error == "retry unavailable"
    assert repeated.warnings == final.warnings
    store.max_document_bytes = 20 * 1024 * 1024
    updated = await store.update_scan(
        doc.scan_id,
        lambda current: current.model_copy(update={"state": "running", "phase": "analysis"}),
    )
    assert (await store.load_scan(doc.scan_id)).revision == updated.revision
    assert (await store.load_scan(doc.scan_id)).phase == "analysis"
    assert not (primary.parent / "terminal.json").exists()


@pytest.mark.asyncio
async def test_progress_cache_does_not_read_full_evidence(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    doc = ScanDocument(scan_id=str(uuid4()), target={"mode": "demo", "hosts": []})
    await store.create_scan(doc)

    def forbidden(*args):
        raise AssertionError("Progress loaded the full report")

    monkeypatch.setattr(store, "_load_scan", forbidden)
    progress = await store.load_progress(doc.scan_id)
    assert progress["scan_id"] == doc.scan_id
    assert "devices" not in progress and "services" not in progress


@pytest.mark.parametrize("failure", ["network", "dhcp", "malformed"])
@pytest.mark.asyncio
async def test_pihole_preserves_healthy_source(failure):
    async def handler(request):
        if request.method == "POST":
            return httpx.Response(200, json={"session": {"valid": True, "sid": "test"}})
        if request.method == "DELETE":
            return httpx.Response(204)
        network = request.url.path.endswith("/devices")
        if network and failure == "network" or not network and failure == "dhcp":
            return httpx.Response(500, json={})
        if not network and failure == "malformed":
            return httpx.Response(200, json={"leases": None})
        if network:
            return httpx.Response(
                200,
                json={
                    "devices": [
                        {
                            "hwaddr": "aa:bb:cc:dd:ee:ff",
                            "ips": [
                                {"ip": "192.168.0.2", "name": "printer", "lastSeen": 1780000000}
                            ],
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "leases": [
                    {
                        "ip": "192.168.0.2",
                        "name": "printer",
                        "hwaddr": "aa:bb:cc:dd:ee:ff",
                        "expires": 0,
                    }
                ]
            },
        )

    records = await PiholeClient(
        "http://192.168.0.1", "test", transport=httpx.MockTransport(handler)
    ).names("192.168.0.0/24")
    assert len(records) == 1 and records[0]["name"] == "printer"
    assert records.warnings[0]["code"] == "PIHOLE_PARTIAL"


def test_discovery_preserves_mac_and_name():
    xml = (
        b'<nmaprun><host><status state="up"/><address addr="192.168.0.2" '
        b'addrtype="ipv4"/><address addr="aa:bb:cc:dd:ee:ff" addrtype="mac" '
        b'vendor="Example"/><hostnames><hostname '
        b'name="printer"/></hostnames></host><runstats><finished '
        b'exit="success"/></runstats></nmaprun>'
    )
    identity = parse_discovery_details(xml, ("192.168.0.2",))["192.168.0.2"]
    assert identity == {"mac": "aa:bb:cc:dd:ee:ff", "vendor": "Example", "hostname": "printer"}


@pytest.mark.asyncio
async def test_discovery_identity_allows_pihole_network_name_match(tmp_path):
    store = JsonStore(tmp_path)
    ip = "192.168.56.10"
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "discover", "cidr": "192.168.56.8/30", "hosts": []},
        policy={"pihole_enabled": True, "allowed_network": "192.168.56.8/30"},
        coverage={"candidate_count": 1, "targets": [{"ip": ip}]},
    )
    await store.create_scan(doc)
    discovery = (
        b'<nmaprun><host><status state="up"/>'
        b'<address addr="192.168.56.10" addrtype="ipv4"/>'
        b'<address addr="aa:bb:cc:dd:ee:ff" addrtype="mac"/>'
        b'<hostnames><hostname name="home-printer"/></hostnames>'
        b'</host><runstats><finished exit="success"/></runstats></nmaprun>'
    )
    host = (Path(__file__).parents[1] / "fixtures" / "nmap_host.xml").read_bytes()
    host = host.replace(b'<hostnames><hostname name="camera-office" /></hostnames>', b"")

    async def runner(args, *_):
        return ProcessResult(discovery if "-sn" in args else host, b"", 0, 0.01)

    class Names:
        async def names(self, scope):
            assert scope == "192.168.56.8/30"
            return [
                {
                    "ip": ip,
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "name": "home-printer",
                    "source": "pihole_network",
                    "observed_at": "2026-09-25T00:00:00Z",
                }
            ]

    supervisor = ScanSupervisor(store, process_runner=runner, pihole_client=Names())
    await supervisor.start(doc.scan_id)
    while supervisor.is_active(doc.scan_id):
        await asyncio.sleep(0.01)
    result = await store.load_scan(doc.scan_id)
    device = result.devices[0]
    assert device.mac == "aa:bb:cc:dd:ee:ff"
    assert device.hostname == "home-printer"
    assert {item["source"] for item in device.name_candidates} == {
        "nmap_discovery",
        "pihole_network",
    }
    assert device.hostname_confidence == "medium"
    assert not device.hostname_conflict


@pytest.mark.asyncio
async def test_ai_partial_rejection_has_field_audit_trail(tmp_path):
    store, doc = await make_stored_scan(tmp_path)

    class PartlyInvalid(ReviewedProvider):
        async def generate(self, payload):
            result = await super().generate(payload)
            result.explanations[-1].title = "Guaranteed safe and secure"
            return result

    result = await ExplanationService(store, PartlyInvalid()).explain_scan(doc.scan_id)
    record = result.explanations[0]
    assert record.status == "ready"
    assert "title" in record.rejected_fields
    assert record.display_title is None
    assert record.content.meaning != doc.findings[0].fixed_explanation.meaning


@pytest.mark.asyncio
async def test_names_added_after_service_checks_update_classification(tmp_path):
    store, doc = await make_stored_scan(tmp_path)
    from app.scanner.pihole import apply_pihole_names

    device = doc.devices[0]
    device.hostname = None
    device.name_candidates = []
    device.hostname_conflict = False
    service = doc.services[0].model_copy(update={"name": "ipp"})
    await store.update_scan(
        doc.scan_id,
        lambda current: current.model_copy(update={"devices": [device], "services": [service]}),
    )
    records = [
        {
            "ip": device.ip,
            "name": "home-printer",
            "mac": "",
            "source": "pihole_dhcp",
            "observed_at": device.observed_at,
        }
    ]
    apply_pihole_names([device], records)
    await store.update_scan(
        doc.scan_id, lambda current: current.model_copy(update={"devices": [device]})
    )
    await ScanSupervisor(store)._enrich_names(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert saved.devices[0].profile.category == "printer"
    add_name(device, "camera", "nmap", device.observed_at)
    await store.update_scan(
        doc.scan_id, lambda current: current.model_copy(update={"devices": [device]})
    )
    await ScanSupervisor(store)._enrich_names(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert saved.devices[0].profile.category == "unknown"
    assert saved.devices[0].profile.conflict


@pytest.mark.asyncio
async def test_host_workers_are_bounded_and_keep_all_checkpoints(tmp_path):
    hosts = ["192.168.56.10", "192.168.56.11", "192.168.56.12"]
    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": hosts},
        coverage={
            "candidate_count": 3,
            "targets": [{"ip": ip, "service_status": "pending"} for ip in hosts],
        },
    )
    await store.create_scan(doc)
    xml = (Path(__file__).parents[1] / "fixtures" / "nmap_host.xml").read_bytes()
    active = 0
    peak = 0
    overlap = asyncio.Event()

    async def runner(args, *_):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        if active == 2:
            overlap.set()
        await asyncio.wait_for(overlap.wait(), timeout=5)
        active -= 1
        return ProcessResult(xml.replace(b"192.168.56.10", args[-1].encode()), b"", 0, 0.05)

    supervisor = ScanSupervisor(store, process_runner=runner)
    await supervisor.start(doc.scan_id)
    while supervisor.is_active(doc.scan_id):
        await asyncio.sleep(0.01)
    final = await store.load_scan(doc.scan_id)
    assert peak == 2
    assert final.state == "completed" and len(final.devices) == 3
    assert final.coverage.service_completed_count == 3


@pytest.mark.asyncio
async def test_host_budget_finishes_with_explicit_incomplete_coverage(tmp_path):
    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": ["192.168.0.2"]},
        coverage={"targets": [{"ip": "192.168.0.2", "service_status": "pending"}]},
    )
    await store.create_scan(doc)

    async def runner(*args):
        await asyncio.sleep(60)

    supervisor = ScanSupervisor(store, process_runner=runner)
    supervisor.host_stage_timeout_s = 0.05
    await supervisor.start(doc.scan_id)
    while supervisor.is_active(doc.scan_id):
        await asyncio.sleep(0.01)
    final = await store.load_scan(doc.scan_id)
    assert final.state == "failed" and final.phase == "finished"
    assert final.coverage.targets[0].reason_code == "scan_time_limit"
    assert final.coverage.service_completed_count == 0
