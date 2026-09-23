"""Short, interface-bound mDNS browsing; advertisements are not security findings."""

from __future__ import annotations

import asyncio
import ipaddress
import threading
from time import monotonic

from app.schemas.scan import DiscoveryObservation

try:
    from zeroconf import IPVersion, ServiceBrowser, ServiceListener, Zeroconf
except ImportError:  # The app remains usable before optional dependencies are installed.
    IPVersion = ServiceBrowser = ServiceListener = Zeroconf = None


SERVICE_TYPES = (
    "_http._tcp.local.",
    "_https._tcp.local.",
    "_ipp._tcp.local.",
    "_printer._tcp.local.",
    "_airplay._tcp.local.",
    "_googlecast._tcp.local.",
    "_hap._tcp.local.",
    "_mqtt._tcp.local.",
)
MAX_ADVERTISEMENTS = 64
MAX_UNIQUE_HOSTS = 8


def mdns_available() -> bool:
    return Zeroconf is not None


def _safe_name(value: str) -> str:
    return "".join(character for character in value if character.isprintable())[:120]


def _browse(scope: str, interface_ip: str, duration_s: float, cancel_event: asyncio.Event):
    if not mdns_available():
        raise RuntimeError("mDNS library is not installed")
    allowed = ipaddress.ip_network(scope, strict=True)
    interface = ipaddress.ip_address(interface_ip)
    if not isinstance(allowed, ipaddress.IPv4Network) or interface not in allowed:
        raise ValueError("mDNS interface is outside the authorised network")
    observations: dict[tuple[str, str, str], DiscoveryObservation] = {}
    observed_ips: set[str] = set()
    guard = threading.Lock()

    class Listener(ServiceListener):
        def add_service(self, zc, type_, name):
            with guard:
                if len(observations) >= MAX_ADVERTISEMENTS:
                    return
            info = zc.get_service_info(type_, name, timeout=300)
            if info is None:
                return
            advertised_name = _safe_name(info.get_name())
            for address_text in info.parsed_addresses(IPVersion.V4Only):
                try:
                    address = ipaddress.IPv4Address(address_text)
                except ValueError:
                    continue
                if address not in allowed:
                    continue
                address_value = str(address)
                key = (address_value, type_, advertised_name)
                with guard:
                    if len(observations) >= MAX_ADVERTISEMENTS:
                        return
                    if address_value not in observed_ips and len(observed_ips) >= MAX_UNIQUE_HOSTS:
                        continue
                    observations[key] = DiscoveryObservation(
                        ip=address_value,
                        advertised_name=advertised_name,
                        service_type=type_,
                    )
                    observed_ips.add(address_value)

        def update_service(self, zc, type_, name):
            self.add_service(zc, type_, name)

        def remove_service(self, zc, type_, name):
            pass

    zc = Zeroconf(interfaces=[interface_ip], ip_version=IPVersion.V4Only)
    browser = None
    try:
        browser = ServiceBrowser(zc, list(SERVICE_TYPES), listener=Listener())
        deadline = monotonic() + duration_s
        while monotonic() < deadline and not cancel_event.is_set():
            threading.Event().wait(min(0.1, deadline - monotonic()))
    finally:
        if browser is not None:
            browser.cancel()
        zc.close()
    return sorted(observations.values(), key=lambda item: (item.ip, item.service_type, item.advertised_name))


async def browse_mdns(
    scope: str, interface_ip: str, cancel_event: asyncio.Event, duration_s: float = 2.5
) -> list[DiscoveryObservation]:
    return await asyncio.to_thread(_browse, scope, interface_ip, duration_s, cancel_event)
