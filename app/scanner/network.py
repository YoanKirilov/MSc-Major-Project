"""Read-only local connection snapshots; no device probes or scope changes."""

import asyncio
import json
import os
import subprocess
import threading
from copy import deepcopy
from time import monotonic


class SnapshotUnavailable(Exception):
    """A local query failed; this is not proof that the network changed."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


_windows_query_lock = threading.Lock()
_windows_query_finished = 0.0
_windows_query_result = None
_windows_query_error = None


def windows_connections(*, strict=False):
    """Share overlapping reads across jobs/status calls, never cache later reads."""
    global _windows_query_finished, _windows_query_result, _windows_query_error
    requested = monotonic()
    if not _windows_query_lock.acquire(timeout=10):
        if strict:
            raise SnapshotUnavailable("adapter_query_busy")
        return None
    try:
        if _windows_query_finished < requested:
            try:
                _windows_query_result = _query_windows_connections()
                _windows_query_error = None
            except SnapshotUnavailable as exc:
                _windows_query_result = None
                _windows_query_error = exc.reason
            _windows_query_finished = monotonic()
        if _windows_query_error and strict:
            raise SnapshotUnavailable(_windows_query_error)
        return deepcopy(_windows_query_result)
    finally:
        _windows_query_lock.release()


def _query_windows_connections():
    """Read once or raise a diagnostic; the public wrapper owns fallback policy."""
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
        if result.returncode:
            raise SnapshotUnavailable("adapter_query_failed")
        if len(result.stdout) > 100_000:
            raise SnapshotUnavailable("adapter_output_invalid")
        rows = json.loads(result.stdout)
        rows = [rows] if isinstance(rows, dict) else rows
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            raise SnapshotUnavailable("adapter_output_invalid")
        return rows
    except subprocess.TimeoutExpired as exc:
        raise SnapshotUnavailable("adapter_query_timeout") from exc
    except ValueError as exc:
        raise SnapshotUnavailable("adapter_output_invalid") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise SnapshotUnavailable("adapter_query_failed") from exc


def connection_snapshot(config, scope, interface=None, *, strict=False):
    from app.config import detect_private_network, nmap_interface_diagnostic

    bound = nmap_interface_diagnostic(config, scope, interface)
    if not bound.get("address"):
        if strict:
            raise SnapshotUnavailable("interface_unavailable")
        return None
    snapshot = {"address": bound["address"], "interface": bound.get("interface", interface)}
    if os.name == "nt":
        rows = windows_connections(strict=True) if strict else windows_connections()
        if rows is None:
            return None
        matched = [
            r
            for r in rows
            if any(a.get("IPAddress") == bound["address"] for a in (r.get("Addresses") or []))
        ]
        if len(matched) != 1:
            if strict:
                raise SnapshotUnavailable("interface_ambiguous")
            return None
        snapshot["connection"] = matched[0]
        snapshot["routed_connections"] = sorted(
            [row for row in rows if any(row.get("Gateways") or [])],
            key=lambda row: str(row.get("Index")),
        )
    else:
        snapshot["default_network"] = detect_private_network()
        if not snapshot["default_network"]:
            if strict:
                raise SnapshotUnavailable("route_unavailable")
            return None
    return snapshot


class NetworkInterrupted(Exception):
    def __init__(self, reason="snapshot_unavailable"):
        self.reason = reason
        super().__init__(reason)


def interruption_message(reason):
    if reason == "network_changed":
        cause = "The network connection changed."
    elif reason == "monitor_delayed":
        cause = "Network monitoring was delayed; the computer may have been suspended."
    else:
        cause = "The app could not verify the current network connection."
    return (
        cause + " Scanning stopped. Confirm your home network before retrying; "
        "saved observations remain available."
    )


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
        self.failure_reason = None
        self._lock = asyncio.Lock()
        self._checked_at = None

    def _fail(self, reason):
        self.failed = True
        self.failure_reason = reason
        raise NetworkInterrupted(reason)

    async def check(self):
        requested_at = monotonic()
        async with self._lock:
            if self.failed:
                raise NetworkInterrupted(self.failure_reason)
            now = monotonic()
            # Check suspension even when sharing an overlapping successful read.
            if now - self.last_tick > 45:
                self._fail("monitor_delayed")
            if self._checked_at is not None and self._checked_at >= requested_at:
                return
            self.last_tick = now
            try:
                observed = await asyncio.to_thread(self.read_context)
            except SnapshotUnavailable as exc:
                self._fail(exc.reason)
            except Exception:
                self._fail("snapshot_query_failed")
            if monotonic() - now > 45:
                self._fail("monitor_delayed")
            if observed is None:
                self._fail("snapshot_unavailable")
            if observed != self.expected:
                self._fail("network_changed")
            self._checked_at = monotonic()
