from __future__ import annotations

import asyncio
import os
import signal
import sys
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


async def _read_limited(stream: asyncio.StreamReader, limit: int) -> tuple[bytes, bool]:
    chunks: list[bytes] = []
    total = 0
    overflow = False
    while True:
        chunk = await stream.read(min(65536, limit + 1))
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            if not overflow:
                chunks.append(chunk[: max(0, limit - (total - len(chunk)))])
            overflow = True
            continue
        if not overflow:
            chunks.append(chunk)
    return b"".join(chunks), overflow


async def _stop_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:
        process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=2)
    except asyncio.TimeoutError:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        await process.wait()


async def run_process(
    args: list[str],
    timeout_s: float,
    cancel_event: asyncio.Event | None = None,
    stdout_limit: int = 8 * 1024 * 1024,
    stderr_limit: int = 64 * 1024,
) -> ProcessResult:
    if not args or any(not isinstance(argument, str) or not argument for argument in args):
        raise ValueError("process arguments must be non-empty strings")
    started = time.monotonic()
    kwargs = {"stdout": asyncio.subprocess.PIPE, "stderr": asyncio.subprocess.PIPE}
    if os.name == "posix":
        kwargs["start_new_session"] = True
    try:
        process = await asyncio.create_subprocess_exec(*args, **kwargs)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"executable not found: {args[0]}") from exc

    stdout_task = asyncio.create_task(_read_limited(process.stdout, stdout_limit))
    stderr_task = asyncio.create_task(_read_limited(process.stderr, stderr_limit))
    wait_task = asyncio.create_task(process.wait())
    cancel_task = asyncio.create_task(cancel_event.wait()) if cancel_event is not None else None
    timed_out = False
    cancelled = False
    overflow = False
    try:
        pending = {wait_task}
        if cancel_task is not None:
            pending.add(cancel_task)
        done, _ = await asyncio.wait(pending, timeout=timeout_s, return_when=asyncio.FIRST_COMPLETED)
        if not done:
            timed_out = True
            await _stop_process(process)
        elif cancel_task is not None and cancel_task in done and cancel_task.result():
            cancelled = True
            await _stop_process(process)
        else:
            await wait_task

        stdout, stdout_overflow = await stdout_task
        stderr, stderr_overflow = await stderr_task
        overflow = stdout_overflow or stderr_overflow
        if overflow and process.returncode is None:
            await _stop_process(process)
        if overflow:
            await process.wait()
        return ProcessResult(
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode,
            duration_s=time.monotonic() - started,
            timed_out=timed_out,
            cancelled=cancelled,
            overflow=overflow,
        )
    finally:
        if cancel_task is not None:
            cancel_task.cancel()
        if process.returncode is None:
            await _stop_process(process)
        for task in (stdout_task, stderr_task, wait_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(stdout_task, stderr_task, wait_task, return_exceptions=True)


if __name__ == "__main__":
    print(sys.argv[1:])
