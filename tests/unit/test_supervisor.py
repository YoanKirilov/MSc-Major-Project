import asyncio
from pathlib import Path

import pytest
from app.jobs.supervisor import ScanSupervisor
from app.scanner.runner import ProcessResult
from app.schemas.scan import (
    DiscoveryObservation,
    ExplanationRecord,
    Finding,
    ScanDocument,
)
from app.schemas.settings import SettingsUpdate
from app.storage.json_store import JsonStore
from tests.fixtures.fixtures import make_telnet_scan

XML = (Path(__file__).parents[1] / "fixtures" / "nmap_host.xml").read_bytes()


@pytest.mark.asyncio
async def test_supervisor_persists_host_checkpoint(tmp_path):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="66666666-6666-4666-8666-666666666666",
        created_at="2020-01-01T00:00:00Z",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        coverage={"targets": [{"ip": "192.168.56.10", "service_status": "pending"}]},
    )
    await store.create_scan(scan)

    async def fake_runner(args, timeout_s, cancel_event):
        return ProcessResult(XML, b"", 0, 0.01)

    supervisor = ScanSupervisor(store, nmap_path="nmap", process_runner=fake_runner)
    await supervisor.start(scan.scan_id)
    while supervisor.is_active(scan.scan_id):
        await asyncio.sleep(0.01)
    saved = await store.load_scan(scan.scan_id)
    assert saved.state == "completed"
    assert saved.started_at != saved.created_at
    assert saved.finished_at != saved.created_at
    assert len(saved.devices) == 1
    assert {finding.rule_id for finding in saved.findings} == {"R01", "R07"}
    assert saved.coverage.service_attempted_count == 1
    assert saved.coverage.service_completed_count == 1
    assert saved.coverage.targets[0].service_status == "completed"


@pytest.mark.asyncio
async def test_supervisor_uses_local_hostname_when_nmap_has_none(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="88888888-8888-4888-8888-888888888888",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        coverage={"targets": [{"ip": "192.168.56.10", "service_status": "pending"}]},
    )
    await store.create_scan(scan)

    async def fake_runner(args, timeout_s, cancel_event):
        return ProcessResult(XML.replace(b' name="camera-office"', b' name=""'), b"", 0, 0.01)

    async def fake_hostname(self, ip):
        return "lab-device.local"

    monkeypatch.setattr(ScanSupervisor, "_local_hostname", fake_hostname)
    supervisor = ScanSupervisor(store, process_runner=fake_runner)
    await supervisor.start(scan.scan_id)
    while supervisor.is_active(scan.scan_id):
        await asyncio.sleep(0.01)
    saved = await store.load_scan(scan.scan_id)
    assert saved.devices[0].hostname == "lab-device.local"


@pytest.mark.asyncio
async def test_supervisor_allows_two_jobs_and_limits_the_third(tmp_path):
    store = JsonStore(tmp_path)
    scan_ids = (
        "77777777-7777-4777-8777-777777777777",
        "99999999-9999-4999-8999-999999999999",
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    )
    for scan_id in scan_ids:
        await store.create_scan(
            ScanDocument(
                scan_id=scan_id,
                target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
            )
        )

    async def waiting_runner(args, timeout_s, cancel_event):
        await cancel_event.wait()
        return ProcessResult(b"", b"", 0, 0.01, cancelled=True)

    supervisor = ScanSupervisor(store, process_runner=waiting_runner, max_concurrent_scans=2)
    await supervisor.start(scan_ids[0])
    await supervisor.start(scan_ids[1])
    assert supervisor.active_scan_count == 2
    assert set(supervisor.active_scan_ids) == set(scan_ids[:2])
    with pytest.raises(RuntimeError, match="SCAN_CAPACITY"):
        await supervisor.start(scan_ids[2])
    await supervisor.shutdown()
    assert supervisor.active_scan_count == 0


@pytest.mark.asyncio
async def test_supervisor_records_failed_host_attempt(tmp_path):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        coverage={"targets": [{"ip": "192.168.56.10", "service_status": "pending"}]},
    )
    await store.create_scan(scan)

    async def failing_runner(args, timeout_s, cancel_event):
        return ProcessResult(b"", b"failure", 1, 0.01)

    supervisor = ScanSupervisor(store, process_runner=failing_runner)
    await supervisor.start(scan.scan_id)
    while supervisor.is_active(scan.scan_id):
        await asyncio.sleep(0.01)

    saved = await store.load_scan(scan.scan_id)
    assert saved.state == "failed"
    assert saved.coverage.service_attempted_count == 1
    assert saved.coverage.service_failed_count == 1
    assert saved.coverage.targets[0].service_status == "failed"
    assert saved.errors[0]["code"] == "HOST_SCAN_FAILED"


@pytest.mark.asyncio
async def test_supervisor_records_discovery_ledger(tmp_path):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        target={"mode": "discover", "cidr": "192.168.56.8/30", "hosts": []},
        coverage={
            "candidate_count": 2,
            "targets": [
                {"ip": "192.168.56.9", "service_status": "pending"},
                {"ip": "192.168.56.10", "service_status": "pending"},
            ],
        },
    )
    await store.create_scan(scan)

    async def fake_runner(args, timeout_s, cancel_event):
        return ProcessResult(XML, b"", 0, 0.01)

    supervisor = ScanSupervisor(store, process_runner=fake_runner)
    await supervisor.start(scan.scan_id)
    while supervisor.is_active(scan.scan_id):
        await asyncio.sleep(0.01)

    saved = await store.load_scan(scan.scan_id)
    by_ip = {target.ip: target for target in saved.coverage.targets}
    assert by_ip["192.168.56.9"].discovery_status == "not_seen"
    assert by_ip["192.168.56.9"].service_status == "skipped"
    assert by_ip["192.168.56.10"].discovery_status == "observed"
    assert by_ip["192.168.56.10"].service_status == "completed"
    assert saved.coverage.service_skipped_count == 1
    assert saved.devices[0].discovery_method == "nmap_discovery"
    assert "nmap_discovery_response" in saved.devices[0].reachability_evidence


@pytest.mark.asyncio
async def test_mdns_advertisement_adds_in_scope_host_without_creating_a_finding(tmp_path):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="12121212-1212-4121-8121-121212121212",
        target={"mode": "discover", "cidr": "192.168.56.8/30", "hosts": []},
        policy={
            "allowed_network": "192.168.56.8/30",
            "mdns_enabled": True,
            "mdns_interface_ip": "192.168.56.9",
        },
        coverage={
            "candidate_count": 2,
            "targets": [
                {"ip": "192.168.56.9", "service_status": "pending"},
                {"ip": "192.168.56.10", "service_status": "pending"},
            ],
        },
    )
    await store.create_scan(scan)

    async def fake_browser(scope, interface_ip, cancel_event):
        assert scope == "192.168.56.8/30"
        assert interface_ip == "192.168.56.9"
        return [
            DiscoveryObservation(
                ip="192.168.56.9", advertised_name="Home printer", service_type="_ipp._tcp.local."
            )
        ]

    async def fake_runner(args, timeout_s, cancel_event):
        if "-sn" in args:
            return ProcessResult(XML, b"", 0, 0.01)
        if args[-1] == "192.168.56.9":
            return ProcessResult(XML.replace(b"192.168.56.10", b"192.168.56.9"), b"", 0, 0.01)
        return ProcessResult(XML, b"", 0, 0.01)

    supervisor = ScanSupervisor(store, process_runner=fake_runner, mdns_browser=fake_browser)
    await supervisor.start(scan.scan_id)
    while supervisor.is_active(scan.scan_id):
        await asyncio.sleep(0.01)
    saved = await store.load_scan(scan.scan_id)
    by_ip = {device.ip: device for device in saved.devices}
    assert saved.coverage.discovered_count == 2
    assert by_ip["192.168.56.9"].discovery_method == "mdns_advertisement"
    assert saved.observations[0].advertised_name == "Home printer"
    assert all(
        finding.service_id in {service.service_id for service in saved.services}
        for finding in saved.findings
    )


@pytest.mark.asyncio
async def test_supervisor_reconciles_interrupted_scan(tmp_path):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        state="running",
        phase="service_scan",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        coverage={"targets": [{"ip": "192.168.56.10", "service_status": "running"}]},
    )
    await store.create_scan(scan)

    supervisor = ScanSupervisor(store)
    await supervisor.reconcile_incomplete()

    saved = await store.load_scan(scan.scan_id)
    assert saved.state == "failed"
    assert saved.phase == "finished"
    assert saved.finished_at is not None
    assert saved.coverage.targets[0].service_status == "cancelled"
    assert saved.errors[-1]["code"] == "SCAN_INTERRUPTED"


@pytest.mark.asyncio
async def test_recovery_finishes_interrupted_ai_analysis_with_fixed_guidance(tmp_path):
    store = JsonStore(tmp_path)
    finding = Finding.model_validate(make_telnet_scan()["finding"])
    scan = ScanDocument(
        scan_id="34343434-3434-4343-8343-343434343434",
        state="completed",
        phase="analysis",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        findings=[finding],
        explanations=[ExplanationRecord(finding_id=finding.finding_id, status="pending")],
    )
    await store.create_scan(scan)
    await ScanSupervisor(store).reconcile_incomplete()
    saved = await store.load_scan(scan.scan_id)
    assert saved.state == "completed"
    assert saved.phase == "finished"
    assert saved.warnings[-1]["code"] == "AI_EXPLANATION_INTERRUPTED"
    assert saved.explanations[0].status == "fallback"
    assert saved.explanations[0].content == finding.fixed_explanation


@pytest.mark.asyncio
async def test_ai_explanation_is_part_of_scan_completion(tmp_path):
    store = JsonStore(tmp_path)
    await store.update_settings(SettingsUpdate(expected_revision=1, ai_enabled=True), 1)
    scan = ScanDocument(
        scan_id="eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        coverage={"targets": [{"ip": "192.168.56.10", "service_status": "pending"}]},
    )
    await store.create_scan(scan)
    started = asyncio.Event()
    release = asyncio.Event()

    class SlowExplanationService:
        async def explain_scan(self, scan_id):
            started.set()
            await release.wait()
            await store.update_scan(
                scan_id, lambda current: current.model_copy(update={"analysis_status": "ready"})
            )

    async def fake_runner(args, timeout_s, cancel_event):
        return ProcessResult(XML, b"", 0, 0.01)

    supervisor = ScanSupervisor(
        store,
        process_runner=fake_runner,
        explanation_service=SlowExplanationService(),
    )
    await supervisor.start(scan.scan_id)
    await started.wait()
    saved = await store.load_scan(scan.scan_id)
    assert supervisor.is_active(scan.scan_id)
    assert saved.state == "running"
    assert saved.phase == "analysis"

    release.set()
    while supervisor.is_analysis_active(scan.scan_id):
        await asyncio.sleep(0.01)
    saved = await store.load_scan(scan.scan_id)
    assert saved.phase == "finished"
    assert saved.state == "completed"


@pytest.mark.asyncio
async def test_saved_report_can_request_ai_without_running_nmap(tmp_path):
    store = JsonStore(tmp_path)
    await store.update_settings(SettingsUpdate(expected_revision=1, ai_enabled=True), 1)
    finding = Finding.model_validate(make_telnet_scan()["finding"])
    scan = ScanDocument(
        scan_id="48484848-4848-4848-8848-484848484848",
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        findings=[finding],
    )
    await store.create_scan(scan)
    started = asyncio.Event()
    release = asyncio.Event()

    class WaitingExplanationService:
        async def explain_scan(self, scan_id):
            started.set()
            await release.wait()

    async def forbidden_runner(*_args):
        raise AssertionError("Rewording a saved report must not run Nmap")

    supervisor = ScanSupervisor(
        store, process_runner=forbidden_runner, explanation_service=WaitingExplanationService()
    )
    await supervisor.request_explanations(scan.scan_id)
    await started.wait()
    during = await store.load_scan(scan.scan_id)
    assert during.state == "running"
    assert during.phase == "analysis"
    with pytest.raises(RuntimeError, match="SCAN_BUSY"):
        await supervisor.request_explanations(scan.scan_id)
    release.set()
    while supervisor.is_analysis_active(scan.scan_id):
        await asyncio.sleep(0.01)
    saved = await store.load_scan(scan.scan_id)
    assert saved.phase == "finished"
    assert saved.findings == scan.findings
    await store.update_scan(
        scan.scan_id,
        lambda current: current.model_copy(
            update={
                "ai_requests_used": 12,
            }
        ),
    )
    await supervisor.request_explanations(scan.scan_id)
    while supervisor.is_analysis_active(scan.scan_id):
        await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_supervisor_cancellation_updates_target_state(tmp_path):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="ffffffff-ffff-4fff-8fff-ffffffffffff",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        coverage={"targets": [{"ip": "192.168.56.10", "service_status": "pending"}]},
    )
    await store.create_scan(scan)
    runner_started = asyncio.Event()

    async def waiting_runner(args, timeout_s, cancel_event):
        runner_started.set()
        await cancel_event.wait()
        return ProcessResult(b"", b"", 1, 0.01, cancelled=True)

    supervisor = ScanSupervisor(store, process_runner=waiting_runner)
    await supervisor.start(scan.scan_id)
    await runner_started.wait()
    assert await supervisor.cancel(scan.scan_id) is True
    while supervisor.is_active(scan.scan_id):
        await asyncio.sleep(0.01)

    saved = await store.load_scan(scan.scan_id)
    assert saved.state == "cancelled"
    assert saved.coverage.targets[0].service_status == "cancelled"
    assert saved.coverage.service_stage_complete is False
