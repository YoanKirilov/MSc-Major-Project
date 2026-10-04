"""Short, interface-bound mDNS browsing; advertisements are not security findings."""

from __future__ import annotations

import asyncio
import ipaddress

from app.schemas.scan import DiscoveryObservation

try:
    from zeroconf import IPVersion, ServiceListener
    from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf
except ImportError:
    IPVersion = ServiceListener = AsyncServiceBrowser = AsyncZeroconf = None


SERVICE_TYPES = (
    "_http._tcp.local.",
    "_https._tcp.local.",
    "_ipp._tcp.local.",
    "_printer._tcp.local.",
    "_airplay._tcp.local.",
    "_googlecast._tcp.local.",
    "_hap._tcp.local.",
    "_mqtt._tcp.local.",
    "_smb._tcp.local.",
    "_device-info._tcp.local.",
    "_ipps._tcp.local.",
    "_raop._tcp.local.",
)
MAX_ADVERTISEMENTS = 64
MAX_UNIQUE_HOSTS = 8
MAX_SERVICE_LOOKUPS = 64
LOOKUP_WORKERS = 4
LOOKUP_TIMEOUT_MS = 750
BROWSE_SECONDS = 4.0


class MdnsObservations(list):
    def __init__(self, values, limited=False):
        super().__init__(values)
        self.warnings = (
            [
                {
                    "code": "MDNS_BUDGET_REACHED",
                    "message": (
                        "The short device-name lookup reached a time or size limit. "
                        "Some names may be missing; this does not affect completed service checks."
                    ),
                }
            ]
            if limited
            else []
        )


def mdns_available() -> bool:
    return AsyncZeroconf is not None


def _safe_name(value: str) -> str:
    return "".join(character for character in value if character.isprintable())[:120]


def safe_properties(properties) -> dict[str, str]:
    """Retain only identification hints, never arbitrary TXT secrets or user IDs."""
    result = {}
    for key in ("fn", "model", "md", "ty", "product", "manufacturer"):
        value = properties.get(key.encode(), properties.get(key))
        if isinstance(value, bytes):
            value = value[:480].decode("utf-8", errors="replace")
        if isinstance(value, str) and (value := _safe_name(value)):
            result[key] = value
    return result


async def browse_mdns(
    scope: str,
    interface_ip: str,
    cancel_event: asyncio.Event,
    duration_s: float = BROWSE_SECONDS,
    target_ips: set[str] | None = None,
    known_ips: set[str] | None = None,
) -> list[DiscoveryObservation]:
    if not mdns_available():
        raise RuntimeError("mDNS library is not installed")
    allowed = ipaddress.ip_network(scope, strict=True)
    interface = ipaddress.ip_address(interface_ip)
    if not isinstance(allowed, ipaddress.IPv4Network) or interface not in allowed:
        raise ValueError("mDNS interface is outside the authorised network")
    if cancel_event.is_set():
        return []
    observations: dict[tuple[str, str, str], DiscoveryObservation] = {}
    observed_ips: set[str] = set()
    tasks: dict[tuple[str, str], asyncio.Task] = {}
    capacity = asyncio.Semaphore(LOOKUP_WORKERS)
    zc = AsyncZeroconf(interfaces=[interface_ip], ip_version=IPVersion.V4Only)
    browser = None
    stopping = False
    limited = False
    known_ips = (known_ips or set()) & (
        target_ips if target_ips is not None else known_ips or set()
    )

    async def resolve(type_, name):
        nonlocal limited
        async with capacity:
            # A timeout does not remove the advertisement from the browser. Retry
            # once here rather than hoping another update event happens to arrive.
            for _ in range(2):
                if stopping or cancel_event.is_set() or len(observations) >= MAX_ADVERTISEMENTS:
                    limited = limited or len(observations) >= MAX_ADVERTISEMENTS
                    return
                try:
                    info = await zc.async_get_service_info(type_, name, timeout=LOOKUP_TIMEOUT_MS)
                    if info is None:
                        continue
                    advertised_name = _safe_name(info.get_name())
                    for address_text in info.parsed_addresses(IPVersion.V4Only):
                        try:
                            address = ipaddress.IPv4Address(address_text)
                        except ValueError:
                            continue
                        if address not in allowed:
                            continue
                        address_value = str(address)
                        if target_ips is not None and address_value not in target_ips:
                            continue
                        if len(observations) >= MAX_ADVERTISEMENTS:
                            return
                        if (
                            address_value not in observed_ips
                            and address_value not in known_ips
                            and len(observed_ips - known_ips) >= MAX_UNIQUE_HOSTS
                        ):
                            limited = True
                            continue
                        observations[(address_value, type_, advertised_name)] = (
                            DiscoveryObservation(
                                ip=address_value,
                                advertised_name=advertised_name,
                                service_type=type_,
                                hostname=_safe_name(info.server or "") or None,
                                port=info.port
                                if isinstance(info.port, int) and 1 <= info.port <= 65535
                                else None,
                                properties=safe_properties(info.properties or {}),
                            )
                        )
                        observed_ips.add(address_value)
                    return
                except (OSError, ValueError, TypeError, AttributeError):
                    # One malformed service must not abort other name lookups.
                    continue

    class Listener(ServiceListener):
        def add_service(self, _zc, type_, name):
            nonlocal limited
            key = (type_, name)
            if key not in tasks and len(tasks) >= MAX_SERVICE_LOOKUPS:
                limited = True
            if not stopping and key not in tasks and len(tasks) < MAX_SERVICE_LOOKUPS:
                # Never block a browser callback waiting for a slow device.
                tasks[key] = asyncio.create_task(resolve(type_, name))

        def update_service(self, _zc, type_, name):
            self.add_service(_zc, type_, name)

        def remove_service(self, _zc, type_, name):
            pass

    try:
        browser = AsyncServiceBrowser(zc.zeroconf, list(SERVICE_TYPES), listener=Listener())
        try:
            await asyncio.wait_for(cancel_event.wait(), timeout=max(0, duration_s))
        except TimeoutError:
            pass
    finally:
        stopping = True
        try:
            if browser is not None:
                await browser.async_cancel()
        finally:
            for task in tasks.values():
                if not task.done():
                    limited = True
                    task.cancel()
            await asyncio.gather(*tasks.values(), return_exceptions=True)
            await zc.async_close()
    return MdnsObservations(
        sorted(
            observations.values(),
            key=lambda item: (item.ip, item.service_type, item.advertised_name),
        ),
        limited=limited,
    )
