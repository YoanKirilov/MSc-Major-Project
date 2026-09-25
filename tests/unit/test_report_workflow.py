import asyncio
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from app.explanations.service import ExplanationService
from app.jobs.supervisor import ScanSupervisor
from app.scanner.runner import ProcessResult
from app.schemas.scan import ScanDocument
from app.storage.json_store import JsonStore
from tests.fixtures.provider import ReviewedProvider

XML = (Path(__file__).parents[1] / "fixtures" / "nmap_host.xml").read_bytes()


async def run_job(store, scan, runner, provider=None):
    await store.create_scan(scan)
    supervisor = ScanSupervisor(
        store,
        process_runner=runner,
        explanation_service=ExplanationService(store, provider or ReviewedProvider()),
    )
    await supervisor.start(scan.scan_id)
    async with asyncio.timeout(10):
        while supervisor.is_active(scan.scan_id):
            await asyncio.sleep(0.01)
    return await store.load_scan(scan.scan_id)


def scan_document(**values):
    return ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
        coverage={
            "candidate_count": 1,
            "targets": [{"ip": "192.168.56.10", "service_status": "pending"}],
        },
        **values,
    )


@pytest.mark.asyncio
async def test_timeout_retry_preserves_single_device_and_correct_coverage(tmp_path):
    attempts = []

    async def runner(args, timeout_s, cancel):
        attempts.append(timeout_s)
        return (
            ProcessResult(b"", b"", 1, 0.01, timed_out=True)
            if len(attempts) == 1
            else ProcessResult(XML, b"", 0, 0.01)
        )

    saved = await run_job(JsonStore(tmp_path), scan_document(), runner)
    assert attempts == [210, 210]
    assert saved.state == "completed" and saved.analysis_status == "ready"
    assert saved.report_explanation.status == "ready"
    assert saved.coverage.service_completed_count == 1
    assert saved.coverage.service_failed_count == 0
    assert saved.coverage.targets[0].attempts == 2
    assert len(saved.devices) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind,code",
    [
        ("timeout", "HOST_SCAN_TIMEOUT"),
        ("error", "HOST_SCAN_FAILED"),
        ("invalid", "HOST_RESULT_INVALID"),
        ("overflow", "HOST_OUTPUT_LIMIT"),
    ],
)
async def test_failed_checks_keep_causes_and_receive_an_ai_overview(tmp_path, kind, code):
    async def runner(*args):
        return ProcessResult(
            b"bad XML",
            b"",
            1 if kind == "error" else 0,
            0.01,
            timed_out=kind == "timeout",
            overflow=kind == "overflow",
        )

    saved = await run_job(JsonStore(tmp_path), scan_document(), runner)
    assert saved.state == "failed"
    assert saved.coverage.targets[0].reason_code == code.lower()
    assert not saved.coverage.service_stage_complete
    assert saved.analysis_status == "ready"
    assert (
        "could not finish checking any devices" in saved.report_explanation.display_limitations[0]
    )


@pytest.mark.asyncio
async def test_model_outage_retains_factual_result_and_clear_retry_status(tmp_path):
    class OfflineProvider(ReviewedProvider):
        calls = 0

        async def generate(self, payload):
            self.calls += 1
            raise httpx.ConnectError("offline")

    provider = OfflineProvider()

    async def runner(*args):
        return ProcessResult(XML, b"", 0, 0.01)

    saved = await run_job(JsonStore(tmp_path), scan_document(), runner, provider)
    assert saved.state == "completed"
    assert saved.analysis_status == "failed"
    assert saved.analysis_error == "provider_unavailable"
    assert saved.devices and saved.findings
    assert provider.calls == 2


@pytest.mark.asyncio
async def test_no_discovered_devices_still_gets_report_explanation(tmp_path):
    scan = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "discover", "cidr": "192.168.56.8/30", "hosts": []},
        coverage={
            "candidate_count": 2,
            "targets": [{"ip": "192.168.56.9"}, {"ip": "192.168.56.10"}],
        },
    )

    async def runner(*args):
        return ProcessResult(
            b'<nmaprun><runstats><finished exit="success"/></runstats></nmaprun>', b"", 0, 0.01
        )

    saved = await run_job(JsonStore(tmp_path), scan, runner)
    assert not saved.findings
    assert saved.analysis_status == "ready" and saved.report_explanation
    assert "cannot tell you about their security" in saved.report_explanation.display_limitations[0]


@pytest.mark.asyncio
async def test_restart_after_collection_preserves_outcome_and_retryable_ai(tmp_path):
    store = JsonStore(tmp_path)
    document = scan_document(
        state="running", phase="analysis", scan_outcome="completed", analysis_status="running"
    )
    await store.create_scan(document)
    await ScanSupervisor(store).reconcile_incomplete()
    saved = await store.load_scan(document.scan_id)
    assert saved.state == "completed"
    assert saved.analysis_status == "failed" and saved.analysis_error == "process_restarted"


@pytest.mark.asyncio
async def test_mdns_only_device_is_advertised_not_a_confirmed_service_response(tmp_path):
    from app.schemas.scan import DiscoveryObservation

    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "discover", "cidr": "192.168.56.8/30", "hosts": []},
        policy={
            "allowed_network": "192.168.56.8/30",
            "mdns_enabled": True,
            "mdns_interface_ip": "192.168.56.9",
        },
        coverage={
            "candidate_count": 2,
            "targets": [{"ip": "192.168.56.9"}, {"ip": "192.168.56.10"}],
        },
    )

    async def runner(args, *rest):
        xml = (
            b"<nmaprun><runstats><finished/></runstats></nmaprun>"
            if "-sn" in args
            else XML.replace(b'state="open"', b'state="filtered"')
        )
        return ProcessResult(xml, b"", 0, 0.01)

    async def advertisements(*args):
        return [
            DiscoveryObservation(
                ip="192.168.56.10",
                advertised_name="Reported printer",
                service_type="_ipp._tcp.local.",
            )
        ]

    await store.create_scan(scan)
    supervisor = ScanSupervisor(store, process_runner=runner, mdns_browser=advertisements)
    await supervisor.start(scan.scan_id)
    async with asyncio.timeout(5):
        while supervisor.is_active(scan.scan_id):
            await asyncio.sleep(0.01)
    saved = await store.load_scan(scan.scan_id)
    assert saved.devices[0].reachability == "advertised"
    assert saved.coverage.targets[1].discovery_sources == ["mdns"]
    assert any(item["source"] == "mdns" for item in saved.devices[0].name_candidates)


@pytest.mark.asyncio
async def test_cancel_saved_analysis_before_task_starts_does_not_leave_running_report(tmp_path):
    store = JsonStore(tmp_path)
    scan = scan_document(state="completed", phase="finished", scan_outcome="completed")
    await store.create_scan(scan)
    service = ExplanationService(store, ReviewedProvider())
    supervisor = ScanSupervisor(store, explanation_service=service)
    await supervisor.request_explanations(scan.scan_id)
    assert await supervisor.cancel(scan.scan_id)
    saved = await store.load_scan(scan.scan_id)
    assert saved.phase == "finished" and saved.state == "cancelled"
    assert saved.analysis_status == "failed"
    assert not supervisor.is_analysis_active(scan.scan_id)
