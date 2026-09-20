import asyncio
import sys

import pytest

from app.scanner.runner import run_process


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
    task = asyncio.create_task(run_process([sys.executable, "-c", "import time; time.sleep(10)"], 10, cancelled))
    await asyncio.sleep(0.05)
    cancelled.set()
    result = await asyncio.wait_for(task, timeout=5)
    assert result.cancelled


@pytest.mark.asyncio
async def test_runner_marks_output_overflow():
    result = await run_process([sys.executable, "-c", "print('x' * 100)"], timeout_s=2, stdout_limit=10)
    assert result.overflow
    assert len(result.stdout) <= 10
