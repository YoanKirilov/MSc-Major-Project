"""Bounded optional identification, not a port scan or proof of device identity."""

import asyncio
from time import monotonic

from app.scanner.mdns import browse_mdns
from app.scanner.names import add_mdns_names, add_name
from app.scanner.reverse_dns import NameResolution, ReverseDnsResolver
from app.schemas.common import iso_z, utc_now
from app.schemas.naming import NameDiagnostic
from app.storage.annotations import NameRefresh


async def lookup_names(device, scope, interface_ip=None, *, browser=browse_mdns, resolver=None):
    copy = device.model_copy(deep=True)
    copy.hostname = None
    copy.name_candidates = []
    notes = []
    checked_at = iso_z(utc_now())
    diagnostics = []
    started = monotonic()

    try:
        value = await asyncio.wait_for(
            (resolver or ReverseDnsResolver().lookup)(device.ip), timeout=5
        )
        if isinstance(value, NameResolution):
            diagnostics.append(value.diagnostic)
            hostname = value.hostname
        else:
            hostname = value
            diagnostics.append(
                NameDiagnostic(
                    source="reverse_dns",
                    status="found" if hostname else "not_found",
                    elapsed_ms=min(60000, round((monotonic() - started) * 1000)),
                )
            )
        add_name(copy, hostname, "reverse_dns", checked_at)
    except (OSError, TimeoutError) as error:
        diagnostics.append(
            NameDiagnostic(
                source="reverse_dns",
                status="timeout" if isinstance(error, TimeoutError) else "error",
                elapsed_ms=min(60000, round((monotonic() - started) * 1000)),
            )
        )
        notes.append("Reverse DNS returned no usable name within its time limit.")
    if interface_ip:
        started = monotonic()
        try:
            observations = await asyncio.wait_for(
                browser(scope, interface_ip, asyncio.Event(), duration_s=3, target_ips={device.ip}),
                timeout=6,
            )
            for item in observations:
                if item.ip == device.ip:
                    add_mdns_names(copy, item)
            found = any(item.get("source") == "mdns" for item in copy.name_candidates)
            diagnostics.append(
                NameDiagnostic(
                    source="mdns",
                    status="found" if found else "not_found",
                    elapsed_ms=min(60000, round((monotonic() - started) * 1000)),
                )
            )
        except (OSError, ValueError, RuntimeError, TimeoutError) as error:
            diagnostics.append(
                NameDiagnostic(
                    source="mdns",
                    status="timeout" if isinstance(error, TimeoutError) else "error",
                    elapsed_ms=min(60000, round((monotonic() - started) * 1000)),
                )
            )
            notes.append("Local announcement lookup was unavailable or timed out.")
    else:
        diagnostics.append(NameDiagnostic(source="mdns", status="not_checked", elapsed_ms=0))
        notes.append("mDNS was not enabled with a validated interface; no announcement lookup ran.")
    if not copy.name_candidates:
        notes.append("No name was found. This does not mean the device is absent or safe.")
    notes.append(
        "These are later claims about this address, not verified identity or new service checks."
    )
    return NameRefresh(
        device_id=device.device_id,
        checked_at=checked_at,
        names=copy.name_candidates[:16],
        notes=notes,
        diagnostics=diagnostics,
    )
