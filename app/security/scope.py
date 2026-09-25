from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from app.scanner.commands import PROFILE_ID

PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(value) for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


@dataclass(frozen=True)
class ValidatedTarget:
    mode: str
    cidr: str | None
    hosts: tuple[str, ...]
    candidates: tuple[str, ...]


def _is_private_rfc1918(network: ipaddress.IPv4Network) -> bool:
    return any(network.subnet_of(allowed) for allowed in PRIVATE_NETWORKS)


def _eligible_hosts(network: ipaddress.IPv4Network) -> tuple[str, ...]:
    if network.prefixlen <= 30:
        return tuple(str(address) for address in network.hosts())
    return tuple(str(address) for address in network)


def validate_target(request: dict, settings: dict) -> ValidatedTarget:
    if request.get("authorised") is not True:
        raise ValueError("authorisation is required")
    if settings.get("profile_id", PROFILE_ID) != PROFILE_ID:
        raise ValueError("unsupported scan profile")
    allowed_text = settings.get("allowed_network")
    if not allowed_text:
        raise ValueError("allowed network is not configured")
    try:
        allowed = ipaddress.ip_network(allowed_text, strict=True)
    except ValueError as exc:
        raise ValueError("configured network is not canonical IPv4 CIDR") from exc
    if not isinstance(allowed, ipaddress.IPv4Network) or not _is_private_rfc1918(allowed):
        raise ValueError("configured network must be RFC1918 IPv4")

    mode = request.get("mode")
    if mode == "discover":
        cidr_text = request.get("cidr")
        if not isinstance(cidr_text, str):
            raise ValueError("discover mode requires a CIDR")
        try:
            target = ipaddress.ip_network(cidr_text, strict=True)
        except ValueError as exc:
            raise ValueError("target CIDR must be canonical IPv4") from exc
        if not isinstance(target, ipaddress.IPv4Network) or not _is_private_rfc1918(target):
            raise ValueError("target must be RFC1918 IPv4")
        if target.prefixlen < 24 or target.prefixlen > 32 or not target.subnet_of(allowed):
            raise ValueError("target is outside the configured network or size limit")
        candidates = _eligible_hosts(target)
        if not candidates:
            raise ValueError("target contains no eligible addresses")
        return ValidatedTarget("discover", str(target), (), candidates)

    if mode == "known_hosts":
        raw_hosts = request.get("hosts")
        if not isinstance(raw_hosts, list) or not raw_hosts:
            raise ValueError("known_hosts mode requires hosts")
        parsed = []
        for raw in raw_hosts:
            try:
                address = ipaddress.ip_address(raw)
            except ValueError as exc:
                raise ValueError("hosts must be canonical IPv4 addresses") from exc
            if not isinstance(address, ipaddress.IPv4Address) or address not in allowed:
                raise ValueError("host is outside the configured network")
            parsed.append(str(address))
        if len(set(parsed)) != len(parsed):
            raise ValueError("duplicate host")
        hosts = tuple(sorted(parsed, key=ipaddress.IPv4Address))
        return ValidatedTarget("known_hosts", None, hosts, hosts)

    raise ValueError("unsupported scan mode")
