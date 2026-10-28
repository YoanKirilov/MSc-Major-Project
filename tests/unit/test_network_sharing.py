"""Fresh cross-job observations and cancellation must preserve scope checks."""

import asyncio
import threading

import pytest
from app.config import AppConfig
from app.scanner.network import (
    FreshNetworkReader,
    NetworkGuard,
    NetworkInterrupted,
    SnapshotUnavailable,
)


async def wait_started(event):
    assert await asyncio.to_thread(event.wait, 3)


@pytest.mark.asyncio
async def test_five_guards_share_one_inflight_read_then_reject_a_new_network(monkeypatch):
    started, release = threading.Event(), threading.Event()
    observed = {"adapter": 1}
    calls = []

    def snapshot(*args, **kwargs):
        calls.append(1)
        started.set()
        assert release.wait(3)
        return dict(observed)

    monkeypatch.setattr("app.scanner.network.connection_snapshot", snapshot)
    reader, config = FreshNetworkReader(), AppConfig()
    guards = [
        NetworkGuard(
            {"adapter": 1}, None, read_async=lambda: reader.read(config, "192.168.56.0/24", "eth1")
        )
        for _ in range(5)
    ]
    tasks = [asyncio.create_task(guard.check()) for guard in guards]
    try:
        await wait_started(started)
        assert reader.shared_count == 4 and len(calls) == 1
    finally:
        release.set()
    await asyncio.gather(*tasks)
    observed["adapter"] = 2
    with pytest.raises(NetworkInterrupted, match="network_changed"):
        await guards[0].check()
    assert len(calls) == 2 and guards[0].failed
    assert reader.diagnostics()["query_ms"] >= 0
    assert reader.diagnostics()["executor_queue_ms"] >= 0
    await reader.close()


@pytest.mark.asyncio
async def test_cancelling_a_waiter_does_not_cancel_another_jobs_read(monkeypatch):
    started, release = threading.Event(), threading.Event()

    def snapshot(*args, **kwargs):
        started.set()
        assert release.wait(3)
        return {"adapter": 1}

    monkeypatch.setattr("app.scanner.network.connection_snapshot", snapshot)
    reader, config = FreshNetworkReader(), AppConfig()
    first = asyncio.create_task(reader.read(config, "192.168.56.0/24", "eth1"))
    second = asyncio.create_task(reader.read(config, "192.168.56.0/24", "eth1"))
    try:
        await wait_started(started)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
    finally:
        release.set()
    assert await second == {"adapter": 1}
    assert reader.query_count == 1 and reader.shared_count == 1
    await reader.close()


@pytest.mark.asyncio
async def test_same_clock_tick_and_different_adapters_do_not_reuse_finished_facts(monkeypatch):
    calls = []

    def snapshot(config, scope, interface, **kwargs):
        calls.append((scope, interface))
        return {"interface": interface}

    monkeypatch.setattr("app.scanner.network.connection_snapshot", snapshot)
    monkeypatch.setattr("app.scanner.network.monotonic", lambda: 10)
    reader, config = FreshNetworkReader(), AppConfig()
    await reader.read(config, "192.168.56.0/24", "eth1")
    await reader.read(config, "192.168.56.0/24", "eth1")
    results = await asyncio.gather(
        reader.read(config, "192.168.56.0/24", "eth2"),
        reader.read(config, "192.168.57.0/24", "eth1"),
    )
    assert results == [{"interface": "eth2"}, {"interface": "eth1"}]
    assert len(calls) == 4


@pytest.mark.asyncio
async def test_shared_timeout_stops_every_guard_and_is_not_cached(monkeypatch):
    started, release = threading.Event(), threading.Event()
    failing = True

    def snapshot(*args, **kwargs):
        started.set()
        assert release.wait(3)
        if failing:
            raise SnapshotUnavailable("list_timeout")
        return {"adapter": 1}

    monkeypatch.setattr("app.scanner.network.connection_snapshot", snapshot)
    reader, config = FreshNetworkReader(), AppConfig()
    guards = [
        NetworkGuard(
            {"adapter": 1}, None, read_async=lambda: reader.read(config, "192.168.56.0/24", "eth1")
        )
        for _ in range(5)
    ]
    tasks = [asyncio.create_task(guard.check()) for guard in guards]
    try:
        await wait_started(started)
    finally:
        release.set()
    errors = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(isinstance(e, NetworkInterrupted) and e.reason == "list_timeout" for e in errors)
    assert all(guard.failed for guard in guards)
    assert reader.query_count == 1 and reader.last_query["reason"] == "list_timeout"
    failing = False
    assert await reader.read(config, "192.168.56.0/24", "eth1") == {"adapter": 1}
    with pytest.raises(NetworkInterrupted):
        await guards[0].check()
    assert reader.query_count == 2
