"""Read-only local connection snapshots; no device probes or scope changes."""

import asyncio
import json
import os
import subprocess
import threading
from copy import deepcopy
from ipaddress import IPv4Address
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
    # Avoid Get-NetIPConfiguration's expensive all-family aggregate. Read only
    # the IPv4/profile/default-route facts the guard uses, in one bounded process.
    # Stop on any cmdlet error: a partial snapshot must never authorise probing.
    command = (
        "$ErrorActionPreference='Stop'; "
        "$taskConnected=@(Get-NetIPInterface -AddressFamily IPv4 "
        "-ConnectionState Connected | Select-Object -ExpandProperty InterfaceIndex); "
        "$taskAddresses=@(Get-NetIPAddress -AddressFamily IPv4); "
        "$taskRoutes=@(Get-NetRoute -AddressFamily IPv4 | "
        "Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' }); "
        "$taskProfiles=@(Get-NetConnectionProfile); "
        "@($taskAddresses | Where-Object { $taskConnected -contains $_.InterfaceIndex } | "
        "Group-Object InterfaceIndex | ForEach-Object { "
        "$taskIndex=[int]$_.Name; "
        "$taskProfile=@($taskProfiles | Where-Object { $_.InterfaceIndex -eq $taskIndex }); "
        "if ($taskProfile.Count -gt 1) { throw 'Ambiguous connection profile' }; "
        "[pscustomobject]@{ Index=$taskIndex; "
        "Profile=if ($taskProfile.Count -eq 1) { $taskProfile[0].Name } else { $null }; "
        "Addresses=@($_.Group | Select-Object IPAddress,PrefixLength); "
        "Gateways=@($taskRoutes | Where-Object { $_.InterfaceIndex -eq $taskIndex } | "
        "Select-Object -ExpandProperty NextHop) } }) | ConvertTo-Json -Depth 5 -Compress"
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
        return _connection_rows(json.loads(result.stdout))
    except subprocess.TimeoutExpired as exc:
        raise SnapshotUnavailable("adapter_query_timeout") from exc
    except ValueError as exc:
        raise SnapshotUnavailable("adapter_output_invalid") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise SnapshotUnavailable("adapter_query_failed") from exc


def _connection_rows(value):
    """Validate and order adapter facts so enumeration order is not a change."""
    rows = [value] if isinstance(value, dict) else value
    if not isinstance(rows, list) or len(rows) > 256:
        raise SnapshotUnavailable("adapter_output_invalid")
    result, indices = [], set()
    try:
        for row in rows:
            if not isinstance(row, dict) or set(row) != {
                "Index",
                "Profile",
                "Addresses",
                "Gateways",
            }:
                raise ValueError("invalid connection fields")
            index, profile = row["Index"], row["Profile"]
            if type(index) is not int or index < 1 or index in indices:
                raise ValueError("invalid or duplicate interface index")
            if profile is not None and (not isinstance(profile, str) or len(profile) > 1024):
                raise ValueError("invalid connection profile")
            if not isinstance(row["Addresses"], list) or not isinstance(row["Gateways"], list):
                raise ValueError("invalid connection arrays")
            addresses = []
            for address in row["Addresses"]:
                if not isinstance(address, dict) or set(address) != {"IPAddress", "PrefixLength"}:
                    raise ValueError("invalid address fields")
                ip, prefix = address["IPAddress"], address["PrefixLength"]
                if not isinstance(ip, str) or type(prefix) is not int or not 0 <= prefix <= 32:
                    raise ValueError("invalid address or prefix")
                addresses.append({"IPAddress": str(IPv4Address(ip)), "PrefixLength": prefix})
            gateways = row["Gateways"]
            if not all(isinstance(gateway, str) for gateway in gateways):
                raise ValueError("invalid gateway")
            result.append(
                {
                    "Index": index,
                    "Profile": profile,
                    "Addresses": sorted(
                        addresses, key=lambda a: (a["IPAddress"], a["PrefixLength"])
                    ),
                    "Gateways": sorted({str(IPv4Address(gateway)) for gateway in gateways}),
                }
            )
            indices.add(index)
    except (ValueError, TypeError) as exc:
        raise SnapshotUnavailable("adapter_output_invalid") from exc
    return sorted(result, key=lambda row: row["Index"])


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
