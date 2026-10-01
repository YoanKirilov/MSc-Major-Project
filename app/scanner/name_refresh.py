"""Bounded optional identification, not a port scan or proof of device identity."""

import asyncio
import socket

from app.scanner.mdns import browse_mdns
from app.scanner.names import add_mdns_names, add_name
from app.schemas.common import iso_z, utc_now
from app.storage.annotations import NameRefresh


async def lookup_names(device, scope, interface_ip=None, *, browser=browse_mdns, resolver=None):
    copy = device.model_copy(deep=True)
    copy.hostname = None
    copy.name_candidates = []
    notes = []
    checked_at = iso_z(utc_now())

    async def default_resolver(ip):
        return (await asyncio.to_thread(socket.gethostbyaddr, ip))[0]

    try:
        hostname = await asyncio.wait_for((resolver or default_resolver)(device.ip), timeout=1)
        add_name(copy, hostname, "reverse_dns", checked_at)
    except (OSError, TimeoutError):
        notes.append("Reverse DNS returned no usable name within its time limit.")
    if interface_ip:
        try:
            observations = await asyncio.wait_for(
                browser(scope, interface_ip, asyncio.Event(), duration_s=3, target_ips={device.ip}),
                timeout=6,
            )
            for item in observations:
                if item.ip == device.ip:
                    add_mdns_names(copy, item)
        except (OSError, ValueError, RuntimeError, TimeoutError):
            notes.append("Local announcement lookup was unavailable or timed out.")
    else:
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
    )
