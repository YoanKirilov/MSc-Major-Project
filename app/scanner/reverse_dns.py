"""Private-address PTR lookups isolated from the shared JSON I/O executor."""

import asyncio
import ipaddress
import json
import sys
from dataclasses import dataclass
from time import monotonic

from app.schemas.naming import NameDiagnostic

from .names import clean_name
from .runner import run_process

# Constant code, isolated Python, validated IP as a separate argument; no shell,
# host-controlled program, user imports, credentials or raw-error output.
WORKER = """import json,socket,sys
try:
    name=socket.gethostbyaddr(sys.argv[1])[0]
except socket.herror:
    print(json.dumps({'status':'not_found'}))
except OSError:
    print(json.dumps({'status':'error'}))
else:
    print(json.dumps({'status':'found','name':name[:255]}))
"""


@dataclass(frozen=True)
class NameResolution:
    hostname: str | None
    diagnostic: NameDiagnostic


class ReverseDnsResolver:
    def __init__(self, *, workers=2, timeout_s=2, queue_timeout_s=1, runner=run_process):
        self.capacity = asyncio.Semaphore(workers)
        self.timeout_s = timeout_s
        self.queue_timeout_s = queue_timeout_s
        self.runner = runner

    async def lookup(self, ip):
        address = ipaddress.IPv4Address(ip)
        if not any(
            address in ipaddress.ip_network(scope)
            for scope in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
        ):
            raise ValueError("Name lookup requires an authorised private IPv4 address")
        started = monotonic()

        def outcome(status, hostname=None):
            return NameResolution(
                hostname,
                NameDiagnostic(
                    source="reverse_dns",
                    status=status,
                    elapsed_ms=min(60000, round((monotonic() - started) * 1000)),
                ),
            )

        try:
            async with asyncio.timeout(self.queue_timeout_s):
                await self.capacity.acquire()
        except TimeoutError:
            return outcome("busy")
        try:
            result = await self.runner(
                [sys.executable, "-I", "-c", WORKER, str(address)],
                self.timeout_s,
                stdout_limit=2048,
                stderr_limit=512,
            )
            if result.timed_out:
                return outcome("timeout")
            if result.cancelled or result.overflow or result.returncode != 0:
                return outcome("error")
            value = json.loads(result.stdout)
            if value.get("status") == "found":
                hostname = clean_name(value.get("name"))
                return outcome("found", hostname) if hostname else outcome("not_found")
            return outcome("not_found" if value.get("status") == "not_found" else "error")
        except (OSError, ValueError, TypeError, AttributeError):
            return outcome("error")
        finally:
            # run_process reaps an owned child on timeout or task cancellation.
            self.capacity.release()
