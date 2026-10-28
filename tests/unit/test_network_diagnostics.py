"""Precise bounded network diagnostics, without probing real adapters or devices."""

import asyncio
import subprocess
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.config import AppConfig, mdns_interface_message, nmap_interface_diagnostic
from app.scanner.network import NetworkGuard, SnapshotUnavailable, connection_snapshot
from app.schemas.scan import ScanDocument


@pytest.mark.parametrize(
    "reason",
    [
        "scanner_unavailable",
        "invalid_scope",
        "list_timeout",
        "list_failed",
        "list_unavailable",
        "list_output_invalid",
        "multiple_matches",
        "interface_unavailable",
        "scope_unmatched",
    ],
)
def test_snapshot_preserves_known_local_interface_failure(monkeypatch, reason):
    monkeypatch.setattr(
        "app.config.nmap_interface_diagnostic", lambda *a, **k: {"address": None, "reason": reason}
    )
    with pytest.raises(SnapshotUnavailable) as error:
        connection_snapshot(None, "192.168.56.0/24", "synthetic", strict=True)
    assert error.value.reason == reason
    assert connection_snapshot(None, "192.168.56.0/24", "synthetic") is None


@pytest.mark.parametrize("reason", [None, "private process output", {"unexpected": True}])
def test_unrecognised_reason_never_becomes_saved_process_output(monkeypatch, reason):
    monkeypatch.setattr(
        "app.config.nmap_interface_diagnostic", lambda *a, **k: {"address": None, "reason": reason}
    )
    with pytest.raises(SnapshotUnavailable, match="^interface_unavailable$"):
        connection_snapshot(None, "192.168.56.0/24", strict=True)


@pytest.mark.parametrize(
    "failure,reason",
    [
        (subprocess.TimeoutExpired("synthetic", 5), "list_timeout"),
        (OSError("synthetic"), "list_unavailable"),
        (SimpleNamespace(returncode=1, stdout="private output"), "list_failed"),
        (SimpleNamespace(returncode=0, stdout="x" * 100001), "list_output_invalid"),
    ],
)
def test_nmap_list_failures_remain_distinct_bounded_and_do_not_guess_scope(
    monkeypatch, failure, reason
):
    calls = []
    monkeypatch.setattr("app.config.resolve_nmap_path", lambda _: "synthetic-nmap")

    def query(*args, **kwargs):
        calls.append(kwargs)
        if isinstance(failure, Exception):
            raise failure
        return failure

    monkeypatch.setattr("app.config.subprocess.run", query)
    assert nmap_interface_diagnostic(AppConfig(), "192.168.56.0/24") == {
        "address": None,
        "reason": reason,
    }
    assert len(calls) == 1 and calls[0]["timeout"] == 5
    message = mdns_interface_message(reason, "192.168.56.0/24", "192.168.56.0/24")
    assert "No active connection matches" not in message
    assert "private output" not in message


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["list_timeout", "list_failed", "multiple_matches"])
async def test_network_failure_saved_exactly_without_retry_or_completed_check(
    tmp_path, monkeypatch, reason
):
    from app.jobs.supervisor import ScanSupervisor
    from app.scanner.runner import ProcessResult
    from app.storage.json_store import JsonStore

    guard = NetworkGuard({"adapter": 1}, lambda: {"adapter": 1})
    monkeypatch.setattr("app.jobs.supervisor.NetworkGuard", lambda *a, **kw: guard)
    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
        policy={"network_context": {"adapter": 1}, "allowed_network": "192.168.56.0/24"},
        coverage={
            "candidate_count": 1,
            "targets": [{"ip": "192.168.56.10", "service_status": "pending"}],
        },
    )
    await store.create_scan(doc)
    calls = []

    async def runner(args, timeout_s, cancel):
        calls.append(args)
        guard.failed, guard.failure_reason = True, reason
        cancel.set()
        return ProcessResult(b"", b"", 1, 0.01, cancelled=True)

    await ScanSupervisor(store, process_runner=runner)._run(doc.scan_id, asyncio.Event())
    saved = await store.load_scan(doc.scan_id)
    assert saved.errors[-1]["reason"] == reason
    assert "network connection changed" not in saved.errors[-1]["message"].lower()
    assert "Scanning stopped" in saved.errors[-1]["message"]
    assert len(calls) == 1 and saved.coverage.service_completed_count == 0
    assert saved.unfinished_device_count == 1 and saved.phase == "finished"
