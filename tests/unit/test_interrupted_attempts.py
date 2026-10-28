"""Sibling interruption must leave one terminal record for each started host."""

import asyncio
from uuid import uuid4

import pytest
from app.explanations.report import report_input
from app.jobs.supervisor import ScanSupervisor
from app.scanner.network import NetworkGuard, NetworkInterrupted
from app.schemas.scan import ScanDocument
from app.storage.json_store import JsonStore


def document():
    hosts = ["192.168.56.10", "192.168.56.11"]
    return ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": hosts},
        policy={
            "allowed_network": "192.168.56.0/24",
            "network_context": {"adapter": 1},
            "extra_details_enabled": True,
        },
        coverage={
            "candidate_count": 2,
            "targets": [{"ip": ip, "service_status": "pending"} for ip in hosts],
        },
    )


def test_failed_overview_explains_missing_assessment_instead_of_a_zero_findings_result():
    doc = document().model_copy(update={"state": "failed", "scan_outcome": "failed"})
    overview, payload = report_input(doc)
    assert "could not be assessed" in overview.fixed_explanation.meaning
    assert "cannot tell you whether" in payload["reviewed_choices"]["meaning"][1]
    assert "0 open" not in overview.fixed_explanation.meaning


@pytest.mark.asyncio
async def test_sibling_guard_failure_finalises_cancelled_process_attempt(tmp_path, monkeypatch):
    store, doc = JsonStore(tmp_path), document()
    await store.create_scan(doc)
    guard = NetworkGuard({"adapter": 1}, lambda: {"adapter": 1})
    monkeypatch.setattr("app.jobs.supervisor.NetworkGuard", lambda *a, **kw: guard)
    started, stopped = asyncio.Event(), asyncio.Event()

    async def runner(args, timeout, cancel):
        if args[-1].endswith(".10"):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()
        await started.wait()
        guard.failed, guard.failure_reason = True, "list_timeout"
        raise NetworkInterrupted("list_timeout")

    supervisor = ScanSupervisor(store, process_runner=runner)
    async with asyncio.timeout(5):
        await supervisor._run(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert stopped.is_set() and saved.state == "failed"
    assert saved.coverage.service_completed_count == 0
    assert saved.coverage.service_attempted_count == 2
    for target in saved.coverage.targets:
        assert target.attempts == len(target.attempt_details) == 1
        terminal = target.attempt_details[0]
        assert terminal.outcome == "NETWORK_INTERRUPTED"
        assert terminal.exit_code is None and terminal.duration_s >= 0
        assert target.reason_code == "network_interrupted"
    assert any(w["code"] == "OPTIONAL_DETAILS_NOT_RUN" for w in saved.warnings)
    assert saved.errors[-1]["reason"] == "list_timeout"
    assert (await store.load_scan(doc.scan_id)).coverage == saved.coverage


@pytest.mark.asyncio
async def test_waiting_for_capacity_does_not_invent_a_started_attempt(tmp_path, monkeypatch):
    store, doc = JsonStore(tmp_path), document()
    await store.create_scan(doc)
    guard = NetworkGuard({"adapter": 1}, lambda: {"adapter": 1})
    monkeypatch.setattr("app.jobs.supervisor.NetworkGuard", lambda *a, **kw: guard)

    async def forbidden(*args):
        pytest.fail("Queued work must not invoke the scanner")

    supervisor = ScanSupervisor(store, process_runner=forbidden)
    supervisor._host_capacity = asyncio.Semaphore(0)
    supervisor.queue_timeout_s = 0.01
    await supervisor._run(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert saved.coverage.service_attempted_count == 0
    assert all(t.attempts == 0 and t.attempt_details == [] for t in saved.coverage.targets)
    assert saved.errors[-1]["code"] == "SCAN_QUEUE_EXPIRED"
