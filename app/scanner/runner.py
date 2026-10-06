from __future__ import annotations

import asyncio
import os
import signal
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessResult:
    stdout: bytes
    stderr: bytes
    returncode: int | None
    duration_s: float
    timed_out: bool = False
    cancelled: bool = False
    overflow: bool = False


class _Capture(asyncio.SubprocessProtocol):
    """Bounded output, with process exit independent of inherited pipe lifetime."""

    def __init__(self, stdout_limit, stderr_limit):
        self.limits = {1: stdout_limit, 2: stderr_limit}
        self.buffers = {1: bytearray(), 2: bytearray()}
        self.overflow = False
        self.exited = asyncio.Event()
        self.closed = asyncio.Event()
        self.error = None

    def pipe_data_received(self, fd, data):
        if fd not in self.buffers:
            return
        available = max(0, self.limits[fd] - len(self.buffers[fd]))
        self.buffers[fd].extend(data[:available])
        self.overflow |= len(data) > available

    def process_exited(self):
        self.exited.set()

    def pipe_connection_lost(self, fd, exc):
        if exc is not None:
            self.error = exc

    def connection_lost(self, exc):
        self.error = self.error or exc
        self.closed.set()


async def _stop_process(transport, capture) -> None:
    # Every wait is bounded; descendants can keep pipes open after the parent exits.
    if os.name == "posix":
        try:
            os.killpg(transport.get_pid(), signal.SIGTERM)
        except ProcessLookupError:
            pass
    elif transport.get_returncode() is None:
        try:
            transport.terminate()
        except ProcessLookupError:
            pass
    try:
        await asyncio.wait_for(capture.exited.wait(), timeout=2)
    except asyncio.TimeoutError:
        if os.name == "posix":
            try:
                os.killpg(transport.get_pid(), signal.SIGKILL)
            except ProcessLookupError:
                pass
    finally:
        # Public transport API closes pipes and kills a still-running direct child.
        transport.close()
    try:
        await asyncio.wait_for(capture.closed.wait(), timeout=2)
    except asyncio.TimeoutError:
        pass  # Never wait forever on OS cleanup; a missing exit code is not success.


async def run_process(
    args: list[str],
    timeout_s: float,
    cancel_event: asyncio.Event | None = None,
    stdout_limit: int = 8 * 1024 * 1024,
    stderr_limit: int = 64 * 1024,
) -> ProcessResult:
    if not args or any(not isinstance(argument, str) or not argument for argument in args):
        raise ValueError("process arguments must be non-empty strings")
    if timeout_s <= 0 or min(stdout_limit, stderr_limit) < 0:
        raise ValueError("positive timeout and non-negative output limits required")
    started = time.monotonic()
    if cancel_event is not None and cancel_event.is_set():
        return ProcessResult(b"", b"", None, time.monotonic() - started, cancelled=True)
    kwargs = {
        "stdin": asyncio.subprocess.DEVNULL,
        "stdout": asyncio.subprocess.PIPE,
        "stderr": asyncio.subprocess.PIPE,
    }
    if os.name == "posix":
        kwargs["start_new_session"] = True
    try:
        capture = _Capture(stdout_limit, stderr_limit)
        transport, _ = await asyncio.get_running_loop().subprocess_exec(
            lambda: capture, *args, **kwargs
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"executable not found: {args[0]}") from exc

    wait_task = asyncio.create_task(capture.closed.wait())
    cancel_task = asyncio.create_task(cancel_event.wait()) if cancel_event is not None else None
    timed_out = False
    cancelled = False
    try:
        pending = {wait_task}
        if cancel_task is not None:
            pending.add(cancel_task)
        done, _ = await asyncio.wait(
            pending,
            timeout=max(0, timeout_s - (time.monotonic() - started)),
            return_when=asyncio.FIRST_COMPLETED,
        )
        if not done:
            timed_out = True
        elif cancel_task is not None and cancel_task in done and cancel_task.result():
            cancelled = True
        else:
            await wait_task

        if timed_out or cancelled:
            await _stop_process(transport, capture)
        elif capture.error:
            raise capture.error
        return ProcessResult(
            stdout=bytes(capture.buffers[1]),
            stderr=bytes(capture.buffers[2]),
            returncode=transport.get_returncode(),
            duration_s=time.monotonic() - started,
            timed_out=timed_out,
            cancelled=cancelled,
            overflow=capture.overflow,
        )
    finally:
        tasks = [wait_task]
        if cancel_task is not None:
            tasks.append(cancel_task)
        if not capture.closed.is_set():
            await _stop_process(transport, capture)
        else:
            transport.close()
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
