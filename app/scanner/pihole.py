"""Optional Pi-hole v6 API reader. No DNS, DHCP or filtering settings are changed."""

from datetime import datetime, timezone
from ipaddress import IPv4Address, ip_address, ip_network
from urllib.parse import urlsplit

import httpx

from app.scanner.names import add_name, clean_name, normalise_mac
from app.schemas.common import iso_z, utc_now


def local_pihole_url(value: str) -> str:
    parsed = urlsplit(value)
    try:
        address = ip_address(parsed.hostname or "")
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Pi-hole URL must use a private IPv4 or loopback IP address") from exc
    local = address.is_loopback or (
        isinstance(address, IPv4Address)
        and any(
            address in ip_network(cidr)
            for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
        )
    )
    if (
        not local
        or parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or port == 0
    ):
        raise ValueError("Pi-hole URL must be a local HTTP(S) origin without credentials or a path")
    return value.rstrip("/")


def timestamp(value) -> str | None:
    try:
        return (
            iso_z(datetime.fromtimestamp(float(value), tz=timezone.utc))
            if float(value) > 0
            else None
        )
    except (TypeError, ValueError, OverflowError, OSError):
        return None


class NameRecords(list):
    """List-compatible result with per-request partial availability notes."""

    def __init__(self, warnings=None):
        super().__init__()
        self.warnings = warnings or []


class PiholeClient:
    def __init__(self, url: str, password: str, *, transport=None):
        self.base_url = local_pihole_url(url)
        self._password = password
        self.transport = transport

    @staticmethod
    async def _json(client, method, path, **kwargs):
        async with client.stream(method, path, **kwargs) as response:
            response.raise_for_status()
            payload = bytearray()
            async for chunk in response.aiter_bytes():
                payload.extend(chunk)
                if len(payload) > 2 * 1024 * 1024:
                    raise ValueError("Pi-hole response exceeds the size limit")
        import json

        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Invalid Pi-hole response")
        return data

    async def names(self, scope: str) -> list[dict[str, str]]:
        network = ip_network(scope, strict=True)
        observed_at = iso_z(utc_now())
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=5,
            trust_env=False,
            follow_redirects=False,
            transport=self.transport,
        ) as client:
            auth = await self._json(client, "POST", "/api/auth", json={"password": self._password})
            session = auth.get("session", {})
            if (
                not isinstance(session, dict)
                or not session.get("valid")
                or not isinstance(session.get("sid"), str)
            ):
                raise ValueError("Pi-hole authentication failed")
            client.headers["X-FTL-SID"] = session["sid"]
            try:
                warnings = []

                async def source(path, key, **kwargs):
                    try:
                        data = await self._json(client, "GET", path, **kwargs)
                        if not isinstance(data.get(key), list):
                            raise ValueError("Invalid source list")
                        return data[key]
                    except (httpx.HTTPError, ValueError):
                        warnings.append(
                            {
                                "code": "PIHOLE_PARTIAL",
                                "message": (
                                    f"Pi-hole {key} could not be read. "
                                    "Other available name sources were kept."
                                ),
                            }
                        )
                        return []

                devices = await source(
                    "/api/network/devices",
                    "devices",
                    params={"max_devices": 1024, "max_addresses": 32},
                )
                leases = await source("/api/dhcp/leases", "leases")
                if len(warnings) == 2:
                    raise ValueError("Pi-hole name sources unavailable")
                records = NameRecords(warnings)

                def add(ip, name, mac, source, seen=None, **extra):
                    try:
                        if ip_address(ip) not in network:
                            return
                    except (ValueError, TypeError):
                        return
                    name = clean_name(name)
                    if name:
                        records.append(
                            {
                                "ip": ip,
                                "name": name,
                                "mac": normalise_mac(mac) or "",
                                "source": source,
                                "observed_at": seen or observed_at,
                                **extra,
                            }
                        )

                # A lease's expiry is not a last-seen timestamp. Ignore expired leases.
                for lease in leases[:4096]:
                    if not isinstance(lease, dict):
                        continue
                    expiry = lease.get("expires")
                    if not isinstance(expiry, (int, float)) or (
                        expiry != 0 and expiry < utc_now().timestamp()
                    ):
                        continue
                    add(
                        lease.get("ip"),
                        lease.get("name"),
                        lease.get("hwaddr"),
                        "pihole_dhcp",
                        expires=timestamp(expiry) or "unlimited",
                    )
                for device in devices[:1024]:
                    if not isinstance(device, dict):
                        continue
                    addresses = device.get("ips", [])
                    if not isinstance(addresses, list):
                        continue
                    for address in addresses[:32]:
                        if not isinstance(address, dict):
                            continue
                        seen = timestamp(address.get("lastSeen"))
                        if seen:
                            add(
                                address.get("ip"),
                                address.get("name"),
                                device.get("hwaddr"),
                                "pihole_network",
                                seen,
                                vendor=clean_name(device.get("macVendor")) or "",
                            )
                return records
            finally:
                try:
                    await client.delete("/api/auth")
                except httpx.HTTPError:
                    pass


def apply_pihole_names(devices, records):
    for device in devices:
        matching = [record for record in records if record["ip"] == device.ip]
        matching.sort(
            key=lambda record: (record["source"] == "pihole_dhcp", record["observed_at"]),
            reverse=True,
        )
        for record in matching:
            mac = normalise_mac(device.mac)
            if mac and record["mac"] and mac != record["mac"]:
                continue
            # Historical IP-only associations are ambiguous after address reuse.
            if record["source"] == "pihole_network" and (not mac or mac != record["mac"]):
                continue
            add_name(
                device,
                record["name"],
                record["source"],
                record["observed_at"],
                matched_by="ip_and_mac" if mac and record["mac"] else "current_lease_ip",
            )
