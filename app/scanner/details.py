"""Bounded identity/web observations shared by Light and Deep; never security verdicts."""

import asyncio
import re
from datetime import datetime, timezone
from ipaddress import IPv4Address, ip_network
from urllib.parse import urljoin, urlsplit

import httpx
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from app.scanner.names import add_name, clean_name
from app.schemas.scan import DeviceDetail

FEATURES = {
    "_http": "Device web page",
    "_https": "Encrypted device web page",
    "_ipp": "Printing",
    "_ipps": "Encrypted printing",
    "_printer": "Printing",
    "_airplay": "AirPlay media sharing",
    "_raop": "Audio streaming",
    "_googlecast": "Media casting",
    "_hap": "Smart-home accessory",
    "_mqtt": "Smart-home messaging",
    "_smb": "File sharing",
    "_device-info": "Device information",
}


def detail(device, kind, label, value, source, status="observed"):
    value = clean_name(value) if kind in {"upnp", "netbios"} else str(value)
    value = value[:600]
    if any(
        (item.kind, item.label, item.value, item.source, item.status)
        == (kind, label, value, source, status)
        for item in device.details
    ):
        return
    if value and len(device.details) < 47:
        device.details.append(
            DeviceDetail(
                kind=kind,
                label=label,
                value=value,
                source=source,
                status=status,
            )
        )
    elif value and len(device.details) == 47:
        device.details.append(
            DeviceDetail(
                kind="web",
                label="Extra information limit",
                value="Some extra details were omitted to keep this report small. "
                "The original scan evidence is unchanged.",
                source="Report limits",
                status="not_checked",
            )
        )


def existing_details(device, services, observations):
    """Interpret facts already collected, without sending requests."""
    for observation in observations:
        if observation.ip != device.ip:
            continue
        feature = FEATURES.get(observation.service_type.split(".")[0], "Device feature")
        detail(device, "mdns", "Advertised feature", feature, "mDNS", "advertised")
        if observation.hostname:
            detail(
                device, "mdns", "Advertised hostname", observation.hostname, "mDNS", "advertised"
            )
        if observation.port:
            detail(
                device,
                "mdns",
                f"Advertised port for {feature}",
                str(observation.port),
                "mDNS",
                "advertised",
            )
        for key, value in observation.properties.items():
            detail(device, "mdns", f"Reported {key}", value, "mDNS", "advertised")
    for service in services:
        for script in service.script_results:
            if script.script_id == "http-title":
                detail(
                    device,
                    "web",
                    f"Web page title (port {service.port})",
                    script.output,
                    "Nmap HTTP title",
                )
            elif script.script_id == "ssl-cert":
                match = re.search(
                    r"Not valid after:\s*(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)", script.output
                )
                if match:
                    try:
                        expiry = datetime.fromisoformat(match[1]).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
                    expired = expiry < datetime.now(timezone.utc)
                    detail(
                        device,
                        "certificate",
                        f"Certificate date (port {service.port})",
                        f"{'Expired' if expired else 'Not expired'}; expiry: {match[1]} UTC. "
                        "This does not verify trust, identity or overall security.",
                        "Nmap certificate",
                    )


def same_device_url(value, ip, scope):
    """No DNS, credentials, cross-device redirects, or external advertised URLs."""
    parsed = urlsplit(value)
    address = IPv4Address(parsed.hostname or "")
    if (
        str(address) != ip
        or address not in ip_network(scope)
        or parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or parsed.fragment
        or parsed.port == 0
    ):
        raise ValueError("URL is not a same-device HTTP(S) address")
    return value


async def fetch(client, url, *, body=False):
    async with client.stream("GET" if body else "HEAD", url) as response:
        data = bytearray()
        if body:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > 65536:
                    raise ValueError("Device description exceeds size limit")
        return response.status_code, response.headers.get("location"), bytes(data)


async def network_details(device, services, scope, *, transport=None):
    """At most two web ports and one UPnP description; no automatic redirects."""
    async with httpx.AsyncClient(
        timeout=2, trust_env=False, follow_redirects=False, transport=transport
    ) as client:
        web = [
            s
            for s in services
            if s.protocol == "tcp"
            and s.state == "open"
            and s.tunnel != "ssl"
            and s.name in {"http", "http-proxy"}
        ][:2]
        for service in web:
            label = f"Web connection (port {service.port})"
            try:
                async with asyncio.timeout(5):
                    url = same_device_url(f"http://{device.ip}:{service.port}/", device.ip, scope)
                    status, location, _ = await fetch(client, url)
                    if 300 <= status < 400 and location:
                        destination = same_device_url(urljoin(url, location), device.ip, scope)
                        if urlsplit(destination).scheme == "https":
                            await fetch(client, destination)
                            message = (
                                "Redirected to HTTPS on this device; the TLS certificate "
                                "passed verification for this address."
                            )
                        else:
                            message = (
                                "Redirected to another HTTP address on this device; "
                                "no HTTPS upgrade was observed."
                            )
                    else:
                        message = (
                            f"The root page answered over HTTP (status {status}); "
                            "no HTTPS redirect was observed in this request."
                        )
                    detail(device, "web", label, message, "Bounded HTTP check")
            except (httpx.HTTPError, ValueError, TimeoutError):
                detail(
                    device,
                    "web",
                    label,
                    "Could not verify an HTTPS upgrade. The device may use a hostname, "
                    "an untrusted certificate, or an unavailable page.",
                    "Bounded HTTP check",
                    "unavailable",
                )
        locations = [
            m[1]
            for s in services
            for script in s.script_results
            if script.script_id == "upnp-info"
            for m in re.finditer(r"(?im)^\s*Location:\s*(\S+)", script.output)
        ]
        if locations:
            try:
                async with asyncio.timeout(4):
                    url = same_device_url(locations[0], device.ip, scope)
                    status, _, body = await fetch(client, url, body=True)
                    if status != 200:
                        raise ValueError("No device description")
                    root = ElementTree.fromstring(body)
                    # Only the root device, not embedded devices with different identities.
                    node = next((n for n in root if n.tag.split("}")[-1] == "device"), None)
                    if node is None:
                        raise ValueError("No root device")
                    for child in node:
                        key = child.tag.split("}")[-1]
                        if key in {"friendlyName", "manufacturer", "modelName", "deviceType"}:
                            value = clean_name(child.text)
                            detail(device, "upnp", key, value, "UPnP description", "advertised")
                            if key == "friendlyName" and value:
                                add_name(device, value, "upnp", device.observed_at)
            except (
                httpx.HTTPError,
                ValueError,
                TimeoutError,
                ElementTree.ParseError,
                DefusedXmlException,
            ):
                detail(
                    device,
                    "upnp",
                    "Device description",
                    "No usable same-device description was obtained.",
                    "UPnP",
                    "unavailable",
                )


async def netbios_name(device, services, nmap_path, runner, cancel, interface=None):
    if device.hostname or not any(
        s.protocol == "tcp" and s.state == "open" and s.port in {139, 445} for s in services
    ):
        return
    args = [
        nmap_path,
        "-n",
        "-Pn",
        "-sU",
        "-p",
        "137",
        "--script",
        "nbstat",
        "--script-timeout",
        "2s",
        "--host-timeout",
        "4s",
        "--max-retries",
        "0",
    ]
    if interface:
        args += ["-e", interface]
    result = await runner([*args, "-oX", "-", device.ip], 5, cancel)
    name = None
    if not (result.timed_out or result.cancelled or result.overflow or result.returncode):
        try:
            root = ElementTree.fromstring(result.stdout)
            for host in root.findall("host"):
                if not any(n.get("addr") == device.ip for n in host.findall("address")):
                    continue
                for script in host.findall("hostscript/script[@id='nbstat']"):
                    match = re.search(r"NetBIOS name:\s*([^,\r\n]+)", script.get("output", ""))
                    if match and match[1] != "<unknown>":
                        name = clean_name(match[1])
        except (ValueError, ElementTree.ParseError, DefusedXmlException):
            pass
    # Never persist raw output: nbstat may also return logged-in usernames.
    if name:
        add_name(device, name, "netbios", device.observed_at)
    detail(
        device,
        "netbios",
        "Computer name",
        name or "No computer name was returned.",
        "NetBIOS",
        "observed" if name else "unavailable",
    )
