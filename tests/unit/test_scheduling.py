import asyncio

import pytest
from app.jobs.scheduling import ExecutionBudget, QueueCancelled, QueueExpired, capacity_slot


@pytest.mark.asyncio
async def test_queue_wait_does_not_spend_execution_budget():
    capacity = asyncio.Semaphore(0)
    budget = ExecutionBudget(0.05)
    calls = []

    async def work():
        async with capacity_slot(capacity):
            async with budget.run():
                calls.append(True)

    task = asyncio.create_task(work())
    await asyncio.sleep(0.08)
    assert not calls
    capacity.release()
    await task
    assert calls == [True]


@pytest.mark.asyncio
async def test_queue_expiry_and_cancellation_do_not_take_slots():
    capacity = asyncio.Semaphore(0)
    with pytest.raises(QueueExpired):
        async with capacity_slot(capacity, timeout_s=0.01):
            pytest.fail("Not admitted")
    cancelled = asyncio.Event()
    cancelled.set()
    with pytest.raises(QueueCancelled):
        async with capacity_slot(capacity, cancel_event=cancelled):
            pytest.fail("Cancelled")
    capacity.release()
    async with capacity_slot(capacity, timeout_s=0.01):
        assert capacity.locked()
    assert not capacity.locked()


@pytest.mark.asyncio
async def test_execution_budget_is_shared_and_not_reset_per_host(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("app.jobs.scheduling.monotonic", lambda: clock[0])
    budget = ExecutionBudget(10)
    async with budget.run():
        clock[0] = 4
    assert budget.remaining == 6
    clock[0] = 100  # Idle time is not charged.
    async with budget.run():
        clock[0] = 107
    assert budget.remaining == -1
    with pytest.raises(TimeoutError):
        async with budget.run():
            await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_five_queued_scans_do_not_expire_execution_budget(tmp_path):
    from pathlib import Path
    from uuid import uuid4

    from app.jobs.supervisor import ScanSupervisor
    from app.scanner.runner import ProcessResult
    from app.schemas.scan import ScanDocument
    from app.storage.json_store import JsonStore

    xml = (Path(__file__).parents[1] / "fixtures/nmap_host.xml").read_bytes()
    store = JsonStore(tmp_path)
    active = 0
    peak = 0

    async def runner(*args):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return ProcessResult(xml, b"", 0, 0.01)

    supervisor = ScanSupervisor(store, process_runner=runner)
    supervisor.host_stage_timeout_s = 1
    await supervisor._host_capacity.acquire()
    await supervisor._host_capacity.acquire()
    ids = []
    for _ in range(5):
        doc = ScanDocument(
            scan_id=str(uuid4()), target={"mode": "known_hosts", "hosts": ["192.168.56.10"]}
        )
        await store.create_scan(doc)
        ids.append(doc.scan_id)
        await supervisor.start(doc.scan_id)
    await asyncio.sleep(1.1)
    assert supervisor.active_scan_count == 5 and peak == 0
    supervisor._host_capacity.release()
    supervisor._host_capacity.release()
    async with asyncio.timeout(10):
        while supervisor.is_active():
            await asyncio.sleep(0.01)
    assert peak <= 2
    for scan_id in ids:
        assert (await store.load_scan(scan_id)).state == "completed"
