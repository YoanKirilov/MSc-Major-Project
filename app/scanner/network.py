"""Read-only local connection snapshots; no device probes or scope changes."""

import asyncio
import json
import os
import subprocess
from time import monotonic


def windows_connections():
    # Property names remain invariant when Windows display labels are translated.
    command = (
        "@(Get-NetIPConfiguration | ForEach-Object { "
        "[pscustomobject]@{ Index=$_.InterfaceIndex; "
        "Profile=$_.NetProfile.Name; "
        "Addresses=@($_.IPv4Address | Select-Object IPAddress,PrefixLength); "
        "Gateways=@($_.IPv4DefaultGateway.NextHop) } }) | ConvertTo-Json -Depth 5 -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode or len(result.stdout) > 100_000:
            return None
        rows = json.loads(result.stdout)
        rows = [rows] if isinstance(rows, dict) else rows
        return rows if isinstance(rows, list) and all(isinstance(r, dict) for r in rows) else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def connection_snapshot(config, scope, interface=None):
    from app.config import detect_private_network, nmap_interface_diagnostic

    bound = nmap_interface_diagnostic(config, scope, interface)
    if not bound.get("address"):
        return None
    snapshot = {"address": bound["address"], "interface": bound.get("interface", interface)}
    if os.name == "nt":
        rows = windows_connections()
        if rows is None:
            return None
        matched = [
            r
            for r in rows
            if any(a.get("IPAddress") == bound["address"] for a in (r.get("Addresses") or []))
        ]
        if len(matched) != 1:
            return None
        snapshot["connection"] = matched[0]
        snapshot["routed_connections"] = sorted(
            [row for row in rows if any(row.get("Gateways") or [])],
            key=lambda row: str(row.get("Index")),
        )
    else:
        snapshot["default_network"] = detect_private_network()
        if not snapshot["default_network"]:
            return None
    return snapshot


class NetworkInterrupted(Exception):
    pass


def host_scan_interface(ip, interface, context):
    """Let Windows route self-scans locally; keep remote probes adapter-bound.

    The caller must retain the network guard using the original bound interface.
    Only the exact address in that verified snapshot qualifies for this exception.
    """
    if (
        os.name == "nt"
        and isinstance(context, dict)
        and context.get("address") == ip
        and context.get("interface") == interface
    ):
        return None
    return interface


class NetworkGuard:
    def __init__(self, expected, read_context):
        self.expected = expected
        self.read_context = read_context
        self.last_tick = monotonic()
        self.failed = False

    async def check(self):
        if self.failed:
            raise NetworkInterrupted
        now = monotonic()
        # Long event-loop suspension must never silently resume target probing.
        if now - self.last_tick > 45:
            self.failed = True
            raise NetworkInterrupted
        self.last_tick = now
        try:
            observed = await asyncio.to_thread(self.read_context)
        except Exception as exc:
            self.failed = True
            raise NetworkInterrupted from exc
        if observed != self.expected:
            self.failed = True
            raise NetworkInterrupted
