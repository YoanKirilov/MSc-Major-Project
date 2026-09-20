import asyncio
from pathlib import Path

import pytest

from app.jobs.supervisor import ScanSupervisor
from app.schemas.scan import ScanDocument, TargetLedgerEntry
from app.scanner.runner import ProcessResult
from app.storage.json_store import JsonStore


XML = (Path(__file__).parents[1] / "fixtures" / "nmap_host.xml").read_bytes()


@pytest.mark.asyncio
async def test_supervisor_persists_host_checkpoint(tmp_path):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id="66666666-6666-4666-8666-666666666666",
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
    assert len(saved.devices) == 1
    assert len(saved.findings) == 1
    assert saved.findings[0].rule_id == "R01"


@pytest.mark.asyncio
async def test_supervisor_rejects_overlapping_jobs(tmp_path):
    store = JsonStore(tmp_path)
    scan_id = "77777777-7777-4777-8777-777777777777"
    await store.create_scan(ScanDocument(scan_id=scan_id, target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]}))
    supervisor = ScanSupervisor(store)
    await supervisor.start(scan_id)
    with pytest.raises(RuntimeError, match="SCAN_BUSY"):
        await supervisor.start(scan_id)
    await supervisor.shutdown()
