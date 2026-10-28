import asyncio
import sys
from time import monotonic
from unittest.mock import AsyncMock

import pytest
from app.scanner.runner import run_process


@pytest.mark.asyncio
async def test_runner_never_spawns_pre_cancelled_work(monkeypatch):
    spawn = AsyncMock(side_effect=AssertionError("Cancelled work must not launch a process"))
    monkeypatch.setattr(asyncio.get_running_loop(), "subprocess_exec", spawn)
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


@pytest.mark.asyncio
async def test_timeout_with_inherited_pipes_preserves_partial_output(monkeypatch):
    loop = asyncio.get_running_loop()
    spawn = loop.subprocess_exec
    output_ready = asyncio.Event()
    ready_at = None

    async def observed_spawn(factory, *args, **kwargs):
        def observed_factory():
            capture = factory()
            receive = capture.pipe_data_received

            def receive_with_ready(fd, data):
                nonlocal ready_at
                receive(fd, data)
                if not output_ready.is_set() and b"captured-before-timeout" in capture.buffers[1]:
                    ready_at = monotonic()
                    output_ready.set()

            capture.pipe_data_received = receive_with_ready
            return capture

        transport, capture = await spawn(observed_factory, *args, **kwargs)
        try:
            # Observe the marker before asserting it was preserved. Cold Python/
            # descendant startup is not evidence that the capture lost output.
            await asyncio.wait_for(output_ready.wait(), 8)
        except BaseException:
            transport.close()
            raise
        return transport, capture

    monkeypatch.setattr(loop, "subprocess_exec", observed_spawn)
    # The child exits naturally in three seconds even if a regression breaks cleanup.
    code = (
        "import subprocess,sys; "
        "subprocess.Popen([sys.executable,'-c','import time; time.sleep(3)']); "
        "print('captured-before-timeout',flush=True)"
    )
    result = await asyncio.wait_for(run_process([sys.executable, "-c", code], 1), 12)
    assert result.timed_out
    assert result.stdout.strip() == b"captured-before-timeout"
    assert ready_at is not None
    assert monotonic() - ready_at < 2.5  # Do not wait for inherited-pipe natural EOF.


@pytest.mark.asyncio
async def test_cancelling_task_closes_process_and_watchers():
    task = asyncio.create_task(run_process([sys.executable, "-c", "import time; time.sleep(3)"], 5))
    await asyncio.sleep(0.1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 5)


@pytest.mark.asyncio
async def test_capture_keeps_stderr_and_reports_overflow():
    result = await run_process(
        [sys.executable, "-c", "import sys; print('out'); print('x'*100,file=sys.stderr)"],
        3,
        stderr_limit=7,
    )
    assert result.stdout.strip() == b"out"
    assert result.stderr == b"xxxxxxx" and result.overflow
