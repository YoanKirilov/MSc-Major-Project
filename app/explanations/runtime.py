"""App-lifetime local Ollama maintenance, without installing or downloading anything."""

import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

import httpx


def ollama_executable():
    found = shutil.which("ollama")
    if found:
        return found
    if os.name == "nt" and os.getenv("LOCALAPPDATA"):
        candidate = Path(os.environ["LOCALAPPDATA"]) / "Programs/Ollama/ollama.exe"
        if candidate.is_file():
            return str(candidate)
    return None


async def launch_local_server(base_url):
    parsed = urlparse(base_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.path
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Automatic startup requires a standard loopback Ollama origin")
    executable = ollama_executable()
    if not executable:
        raise FileNotFoundError("Ollama is not installed")
    host = "[::1]" if parsed.hostname == "::1" else "127.0.0.1"
    environment = {
        **os.environ,
        "OLLAMA_HOST": f"{host}:{parsed.port or 11434}",
        "OLLAMA_NO_CLOUD": "1",
    }
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    return await asyncio.create_subprocess_exec(
        executable,
        "serve",
        env=environment,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        **options,
    )


class OllamaRuntime:
    """Only an owned server is stopped. Existing tray/services remain untouched."""

    def __init__(self, provider, *, launcher=launch_local_server):
        self.provider = provider
        self.launcher = launcher
        self.process = None
        self.task = None
        self.state = "starting"
        self.next_start = 0.0
        self.next_warm = 0.0
        self.lock = asyncio.Lock()

    def start(self):
        if self.task is None:
            self.task = asyncio.create_task(self._maintain(), name="ollama-maintenance")

    async def wait_ready(self, timeout_s=150):
        # Windows hardware discovery can outlast a normal HTTP health timeout.
        # Give startup a bounded grace period instead of two immediate failures.
        try:
            async with asyncio.timeout(timeout_s):
                while True:
                    if await self.ensure_ready():
                        return True
                    if self.state in {"missing_model", "not_installed", "startup_failed", "error"}:
                        return False
                    await asyncio.sleep(2)
        except TimeoutError:
            self.state = "startup_timeout"
            return False

    async def ensure_ready(self, *, warm=False):
        async with self.lock:
            ready = await self.provider.available()
            if not ready:
                state = (self.provider.last_readiness or {}).get("state", "unavailable")
                self.state = state
                if state != "unreachable":
                    return False
                if self.process is not None and self.process.returncode is not None:
                    await self.process.wait()
                    self.process = None
                if self.process is None and monotonic() >= self.next_start:
                    self.next_start = monotonic() + 60
                    try:
                        launching = asyncio.create_task(self.launcher(self.provider.base_url))
                        try:
                            self.process = await asyncio.shield(launching)
                        except asyncio.CancelledError:
                            # Do not orphan a just-started child during app shutdown.
                            try:
                                self.process = await launching
                            except (OSError, ValueError):
                                pass
                            # A failed launch must not swallow shutdown cancellation
                            # and leave the maintenance loop running indefinitely.
                            raise
                    except FileNotFoundError:
                        self.state = "not_installed"
                        return False
                    except (OSError, ValueError):
                        self.state = "startup_failed"
                        return False
                if self.process is None:
                    return False
                self.state = "starting"
                for _ in range(12):
                    await asyncio.sleep(0.5)
                    if await self.provider.available():
                        ready = True
                        break
                    if self.process.returncode is not None:
                        break
            if not ready:
                return False
            self.state = "ready"
            if warm and monotonic() >= self.next_warm:
                self.state = "warming"
                await self.provider.preload()
                self.next_warm = monotonic() + 300
                self.state = "ready"
            return True

    async def _maintain(self):
        while True:
            try:
                await self.ensure_ready(warm=True)
            except (httpx.HTTPError, TimeoutError, ValueError, TypeError, AttributeError):
                self.state = "preload_failed"
            await asyncio.sleep(30)

    async def close(self):
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        if self.process is not None:
            if self.process.returncode is None:
                try:
                    self.process.terminate()
                except ProcessLookupError:
                    pass
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except TimeoutError:
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass
                await self.process.wait()
            self.process = None
