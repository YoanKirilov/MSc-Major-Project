import asyncio
import sys
from unittest.mock import AsyncMock

import pytest
from app.scanner.runner import run_process


@pytest.mark.asyncio
async def test_runner_never_spawns_pre_cancelled_work(monkeypatch):
    spawn = AsyncMock(side_effect=AssertionError("Cancelled work must not launch a process"))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    cancelled = asyncio.Event()
    cancelled.set()
    result = await run_process([sys.executable, "-c", "print('must not run')"], 2, cancelled)
    spawn.assert_not_called()
    assert result.cancelled and result.returncode is None
    assert result.stdout == result.stderr == b""
    assert not result.timed_out and not result.overflow


@pytest.mark.asyncio
async def test_runner_awaits_cancellation_watcher_cleanup():
    class TrackedEvent(asyncio.Event):
        cleaned = False

        async def wait(self):
            try:
                await super().wait()
            finally:
                self.cleaned = True

    event = TrackedEvent()
    result = await run_process([sys.executable, "-c", "print('done')"], 5, event)
    assert result.returncode == 0
    assert event.cleaned


@pytest.mark.asyncio
async def test_runner_captures_output_without_shell():
    result = await run_process([sys.executable, "-c", "print('safe-output')"], timeout_s=2)
    assert result.returncode == 0
    assert result.stdout.strip() == b"safe-output"
    assert not result.timed_out


@pytest.mark.asyncio
async def test_runner_stops_timeout():
    result = await run_process([sys.executable, "-c", "import time; time.sleep(10)"], timeout_s=0.1)
    assert result.timed_out
    assert result.returncode is not None


@pytest.mark.asyncio
async def test_runner_stops_on_cancellation():
    cancelled = asyncio.Event()
    task = asyncio.create_task(
        run_process([sys.executable, "-c", "import time; time.sleep(10)"], 10, cancelled)
    )
    await asyncio.sleep(0.05)
    cancelled.set()
    result = await asyncio.wait_for(task, timeout=5)
    assert result.cancelled


@pytest.mark.asyncio
async def test_runner_marks_output_overflow():
    result = await run_process(
        [sys.executable, "-c", "print('x' * 100)"], timeout_s=2, stdout_limit=10
    )
    assert result.overflow
    assert len(result.stdout) <= 10
