import asyncio
import subprocess
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.explanations.report import report_input
from app.scanner.network import NetworkGuard, NetworkInterrupted, SnapshotUnavailable
from app.schemas.scan import ScanDocument


@pytest.mark.asyncio
async def test_guard_shares_only_overlapping_reads():
    entered, release = threading.Event(), threading.Event()
    calls = []

    def read():
        calls.append(1)
        entered.set()
        assert release.wait(3)
        return {"adapter": 1}

    guard = NetworkGuard({"adapter": 1}, read)
    first = asyncio.create_task(guard.check())
    assert await asyncio.to_thread(entered.wait, 3)
    others = [asyncio.create_task(guard.check()) for _ in range(3)]
    await asyncio.sleep(0)
    release.set()
    await asyncio.gather(first, *others)
    assert len(calls) == 1
    await guard.check()
    assert len(calls) == 2  # No stale cache for later probes.


@pytest.mark.asyncio
async def test_windows_adapter_queries_are_shared_across_callers(monkeypatch):
    from app.scanner import network

    entered, release = threading.Event(), threading.Event()
    calls = []

    def query(**kwargs):
        calls.append(1)
        entered.set()
        assert release.wait(3)
        return [{"Index": 1}]

    monkeypatch.setattr(network, "_query_windows_connections", query)
    first = asyncio.create_task(asyncio.to_thread(network.windows_connections, strict=True))
    assert await asyncio.to_thread(entered.wait, 3)
    others = [
        asyncio.create_task(asyncio.to_thread(network.windows_connections, strict=True))
        for _ in range(3)
    ]
    await asyncio.sleep(0.05)
    release.set()
    results = await asyncio.gather(first, *others)
    assert len(calls) == 1
    results[0][0]["Index"] = 2
    assert results[1] == [{"Index": 1}]
    assert await asyncio.to_thread(network.windows_connections) == [{"Index": 1}]
    assert len(calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["adapter_query_timeout", "adapter_output_invalid"])
async def test_guard_latches_structured_query_failure(reason):
    def read():
        raise SnapshotUnavailable(reason)

    guard = NetworkGuard({"adapter": 1}, read)
    for _ in range(2):
        with pytest.raises(NetworkInterrupted) as error:
            await guard.check()
        assert error.value.reason == reason
    assert guard.failed and guard.failure_reason == reason


@pytest.mark.asyncio
async def test_guard_distinguishes_unavailable_from_changed():
    for observed, reason in [(None, "snapshot_unavailable"), ({"adapter": 2}, "network_changed")]:
        guard = NetworkGuard({"adapter": 1}, lambda observed=observed: observed)
        with pytest.raises(NetworkInterrupted) as error:
            await guard.check()
        assert error.value.reason == reason


def test_windows_query_timeout_is_diagnostic_only_in_strict_mode(monkeypatch):
    from app.scanner.network import windows_connections

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("adapter query", 8)

    monkeypatch.setattr("app.scanner.network.subprocess.run", timeout)
    assert windows_connections() is None
    with pytest.raises(SnapshotUnavailable, match="adapter_query_timeout"):
        windows_connections(strict=True)


@pytest.mark.parametrize(
    "reply,reason",
    [
        (SimpleNamespace(returncode=1, stdout=""), "adapter_query_failed"),
        (SimpleNamespace(returncode=0, stdout="not-json"), "adapter_output_invalid"),
        (SimpleNamespace(returncode=0, stdout="null"), "adapter_output_invalid"),
        (SimpleNamespace(returncode=0, stdout="[1]"), "adapter_output_invalid"),
        (SimpleNamespace(returncode=0, stdout="x" * 100001), "adapter_output_invalid"),
        (OSError("query could not start"), "adapter_query_failed"),
    ],
)
def test_windows_query_public_fallback_and_diagnostics(monkeypatch, reply, reason):
    from app.scanner.network import windows_connections

    def query(*args, **kwargs):
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr("app.scanner.network.subprocess.run", query)
    assert windows_connections() is None
    with pytest.raises(SnapshotUnavailable) as error:
        windows_connections(strict=True)
    assert error.value.reason == reason


@pytest.mark.parametrize("mode", ["discover", "known_hosts"])
@pytest.mark.parametrize("status", ["cancelled", "pending", "failed", "timed_out", "skipped"])
def test_report_counts_every_unfinished_selected_check(mode, status):
    target = {
        "mode": mode,
        **(
            {"cidr": "192.168.0.0/24"}
            if mode == "discover"
            else {"hosts": ["192.168.0.2", "192.168.0.3"]}
        ),
    }
    targets = [
        {"ip": "192.168.0.2", "discovery_status": "observed", "service_status": "completed"},
        {"ip": "192.168.0.3", "discovery_status": "observed", "service_status": status},
    ]
    if mode == "discover":
        targets.append(
            {"ip": "192.168.0.4", "discovery_status": "not_seen", "service_status": "skipped"}
        )
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target=target,
        state="partial",
        coverage={
            "candidate_count": 254 if mode == "discover" else 2,
            "discovered_count": 2,
            "service_completed_count": 1,
            "service_failed_count": 0,
            "targets": targets,
        },
    )
    assert doc.unfinished_device_count == 1
    finding, payload = report_input(doc)
    assert "unfinished: 1" in finding.fixed_explanation.how_to_check[0]
    assert "for 1 device." in payload["reviewed_choices"]["how_to_check"][0][1]
    assert "retry unfinished" in finding.fixed_explanation.recommended_steps[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("network_failure", [False, True])
async def test_active_host_cancellation_preserves_origin(tmp_path, monkeypatch, network_failure):
    from app.jobs.supervisor import ScanSupervisor
    from app.scanner.runner import ProcessResult
    from app.storage.json_store import JsonStore

    guard = NetworkGuard({"adapter": 1}, lambda: {"adapter": 1})
    monkeypatch.setattr("app.jobs.supervisor.NetworkGuard", lambda *a: guard)
    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": ["192.168.0.2"]},
        policy={"network_context": {"adapter": 1}, "allowed_network": "192.168.0.0/24"},
        coverage={
            "candidate_count": 1,
            "targets": [{"ip": "192.168.0.2", "service_status": "pending"}],
        },
    )
    await store.create_scan(doc)

    async def runner(args, timeout_s, cancel_event):
        if network_failure:
            guard.failed = True
            guard.failure_reason = "adapter_query_timeout"
        cancel_event.set()
        return ProcessResult(b"", b"", 1, 0.1, cancelled=True)

    await ScanSupervisor(store, process_runner=runner)._run(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    target = saved.coverage.targets[0]
    assert target.reason_code == (
        "network_interrupted" if network_failure else "host_scan_cancelled"
    )
    assert target.attempt_details[0].outcome == (
        "NETWORK_INTERRUPTED" if network_failure else "HOST_SCAN_CANCELLED"
    )
    assert saved.unfinished_device_count == 1
    if network_failure:
        assert saved.errors[-1]["reason"] == "adapter_query_timeout"
        assert "could not verify" in saved.errors[-1]["message"]
    else:
        assert saved.state == "cancelled" and not saved.errors
