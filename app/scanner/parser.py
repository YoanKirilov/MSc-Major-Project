from __future__ import annotations

import re
from collections.abc import Collection
from uuid import NAMESPACE_URL, uuid5

from defusedxml import ElementTree

from app.scanner.commands import PORTS, UDP_PORTS
from app.schemas.scan import Device, Service

SCRIPT_OUTPUT_LIMIT = 1024


class HostUnreachable(ValueError):
    """A completed Nmap run explicitly reports no reachable host, not broken XML."""


def host_failure_detail(error: ValueError) -> str:
    """Expose only reviewed parser diagnostics, never raw device-controlled output."""
    return {
        "host not reachable": (
            "Nmap could not reach this device for checking. It may be asleep, disconnected "
            "or not responding; the cause was not established."
        ),
        "malformed host XML": "Nmap returned unreadable scan data.",
        "unexpected XML root": "Nmap returned an unexpected result format.",
        "scan XML is incomplete": "Nmap did not return a completion record.",
        "Nmap reported an unsuccessful scan": (
            "Nmap reported that its scan did not finish successfully."
        ),
        "host XML must contain exactly one host": (
            "Nmap did not return exactly one device record for this check."
        ),
        "host XML contains an unexpected target": (
            "The returned device address did not match the requested address."
        ),
        "host scan timed out": "Nmap ran out of time while checking this device.",
        "conflicting duplicate port record": "Nmap returned conflicting connection results.",
        "conflicting summarized port record": "Nmap returned conflicting connection results.",
    }.get(str(error), "The returned scan data could not be validated.")


def _extra_port_states(ports, tcp_ports, udp_ports):
    """Use explicit protocol/port lists only; aggregate counts are ambiguous."""
    result = {}
    for group in ports.findall("extraports"):
        state = group.get("state", "unknown").replace("|", "_")
        if state not in {"closed", "filtered", "open_filtered", "closed_filtered"}:
            continue
        for reason in group.findall("extrareasons"):
            protocol = reason.get("proto")
            if protocol not in {"tcp", "udp"}:
                continue
            selected = tcp_ports if protocol == "tcp" else udp_ports
            values = set()
            for part in reason.get("ports", "").split(","):
                if not re.fullmatch(r"[0-9]{1,5}(?:-[0-9]{1,5})?", part):
                    break
                bounds = [int(value) for value in part.split("-")]
                first, last = bounds[0], bounds[-1]
                if not 1 <= first <= last <= 65535:
                    break
                values.update(range(first, last + 1))
            else:
                if reason.get("count") != str(len(values)):
                    continue
                for port in values:
                    if port not in selected:
                        continue
                    key = (protocol, port)
                    value = (state, _text(reason, "reason"))
                    if key in result and result[key] != value:
                        raise ValueError("conflicting summarized port record")
                    result[key] = value
    return result


def _text(element, attribute: str, limit: int = 255) -> str | None:
    value = element.attrib.get(attribute)
    if value is None:
        return None
    cleaned = "".join(char for char in value if char >= " " or char in "\t\n\r")
    return cleaned[:limit] or None


def _script_results(element) -> list[dict[str, str | bool]]:
    if element is None:
        return []
    results = []
    for script in element.findall("script")[:32]:
        script_id = _text(script, "id")
        output = _text(script, "output", SCRIPT_OUTPUT_LIMIT)
        if script_id and output:
            results.append(
                {
                    "script_id": script_id,
                    "output": output,
                    "truncated": len(script.attrib.get("output", "")) > SCRIPT_OUTPUT_LIMIT,
                }
            )
    return results


def _require_completed(root):
    if root.tag != "nmaprun":
        raise ValueError("unexpected XML root")
    runstats = root.find("runstats")
    finished = runstats is not None and runstats.find("finished") is not None
    if not finished:
        raise ValueError("scan XML is incomplete")
    if runstats.find("finished").attrib.get("exit", "success") != "success":
        raise ValueError("Nmap reported an unsuccessful scan")


def parse_discovery(xml_bytes: bytes, candidates: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(parse_discovery_details(xml_bytes, candidates)))


def parse_discovery_details(xml_bytes: bytes, candidates: tuple[str, ...]) -> dict[str, dict]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except Exception as exc:
        raise ValueError("malformed discovery XML") from exc
    _require_completed(root)
    allowed = set(candidates)
    observed = {}
    for host in root.findall("host"):
        address = host.find("address[@addrtype='ipv4']")
        if address is None or address.attrib.get("addr") not in allowed:
            raise ValueError("discovery XML contains an unexpected target")
        status = host.find("status")
        if status is not None and status.attrib.get("state") == "up":
            mac = host.find("address[@addrtype='mac']")
            hostname = host.find("hostnames/hostname")
            observed[address.attrib["addr"]] = {
                "mac": _text(mac, "addr") if mac is not None else None,
                "vendor": _text(mac, "vendor") if mac is not None else None,
                "hostname": _text(hostname, "name") if hostname is not None else None,
            }
    return observed


def parse_host(
    xml_bytes: bytes,
    expected_ip: str,
    scan_id: str,
    discovery_method: str = "known_host",
    profile_tcp_ports: Collection[int] = PORTS,
    profile_udp_ports: Collection[int] = UDP_PORTS,
    fill_unknown: bool = True,
) -> tuple[Device, list[Service]]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except Exception as exc:
        raise ValueError("malformed host XML") from exc
    _require_completed(root)
    hosts = root.findall("host")
    if not hosts:
        counts = root.find("runstats/hosts")
        if counts is not None and all(
            counts.get(key) == value
            for key, value in {"up": "0", "down": "1", "total": "1"}.items()
        ):
            raise HostUnreachable("host not reachable")
    if len(hosts) != 1:
        raise ValueError("host XML must contain exactly one host")
    host = hosts[0]
    if host.attrib.get("timedout") == "true":
        raise ValueError("host scan timed out")
    address = host.find("address[@addrtype='ipv4']")
    if address is None or address.attrib.get("addr") != expected_ip:
        raise ValueError("host XML contains an unexpected target")
    status = host.find("status")
    if status is not None and status.get("state") == "down":
        raise HostUnreachable("host not reachable")

    device_id = str(uuid5(uuid5(NAMESPACE_URL, scan_id), f"device:{expected_ip}"))
    hostnames = host.find("hostnames/hostname")
    mac_address = host.find("address[@addrtype='mac']")
    device = Device(
        device_id=device_id,
        scan_id=scan_id,
        ip=expected_ip,
        hostname=_text(hostnames, "name") if hostnames is not None else None,
        hostname_source="nmap" if hostnames is not None and _text(hostnames, "name") else None,
        mac=_text(mac_address, "addr") if mac_address is not None else None,
        vendor=_text(mac_address, "vendor") if mac_address is not None else None,
        discovery_method=discovery_method,
        reachability="unconfirmed",
        reachability_evidence=[],
        host_script_results=_script_results(host.find("hostscript")),
    )
    parsed: dict[tuple[str, int], Service] = {}
    ports = host.find("ports")
    if ports is not None:
        for port_node in ports.findall("port"):
            protocol = port_node.attrib.get("protocol")
            if protocol not in {"tcp", "udp"}:
                continue
            try:
                port = int(port_node.attrib["portid"])
            except (KeyError, ValueError):
                continue
            profile_ports = profile_tcp_ports if protocol == "tcp" else profile_udp_ports
            if port not in profile_ports:
                continue
            state_node = port_node.find("state")
            state_value = (
                state_node.attrib.get("state", "unknown") if state_node is not None else "unknown"
            )
            state_value = {
                "open|filtered": "open_filtered",
                "closed|filtered": "closed_filtered",
            }.get(state_value, state_value)
            if state_value not in {
                "open",
                "closed",
                "filtered",
                "open_filtered",
                "closed_filtered",
                "unfiltered",
                "unknown",
            }:
                state_value = "unknown"
            service_node = port_node.find("service")
            method = "unknown"
            confidence = None
            name = None
            product = version = extra_info = tunnel = None
            if service_node is not None:
                name = _text(service_node, "name")
                product = _text(service_node, "product")
                version = _text(service_node, "version")
                extra_info = _text(service_node, "extrainfo")
                tunnel_value = _text(service_node, "tunnel")
                tunnel = "ssl" if tunnel_value == "ssl" else None
                method = "probed" if service_node.attrib.get("method") == "probed" else "table"
                try:
                    confidence = int(service_node.attrib["conf"])
                except (KeyError, ValueError):
                    confidence = None
            service_id = str(uuid5(uuid5(NAMESPACE_URL, device_id), f"{protocol}:{port}"))
            parsed_service = Service(
                service_id=service_id,
                device_id=device_id,
                protocol=protocol,
                port=port,
                state=state_value,
                state_reason=_text(state_node, "reason") if state_node is not None else None,
                name=name,
                product=product,
                version=version,
                extra_info=extra_info,
                detection_method=method,
                nmap_confidence=confidence,
                tunnel=tunnel,
                script_results=_script_results(port_node),
            )
            key = (protocol, port)
            if key in parsed and parsed[key].model_dump(
                exclude={"observed_at"}
            ) != parsed_service.model_dump(exclude={"observed_at"}):
                raise ValueError("conflicting duplicate port record")
            parsed[key] = parsed_service
            if state_value in {"open", "closed", "unfiltered"}:
                device.reachability = "observed"
                device.reachability_evidence = [
                    "open_port_response" if state_value == "open" else "closed_port_response"
                ]
        summarized = _extra_port_states(ports, profile_tcp_ports, profile_udp_ports)
        for (protocol, port), (state, reason) in summarized.items():
            explicit = parsed.get((protocol, port))
            if explicit is not None and explicit.state != state:
                raise ValueError("conflicting summarized port record")
            if state == "closed":
                device.reachability = "observed"
                if "closed_port_response" not in device.reachability_evidence:
                    device.reachability_evidence.append("closed_port_response")
            # Deep scans omit bulk non-open slots to keep reports bounded.
            if fill_unknown and explicit is None:
                parsed[(protocol, port)] = Service(
                    service_id=str(uuid5(uuid5(NAMESPACE_URL, device_id), f"{protocol}:{port}")),
                    device_id=device_id,
                    protocol=protocol,
                    port=port,
                    state=state,
                    state_reason=reason,
                )
    if fill_unknown:
        services = [
            parsed.get((protocol, port))
            or Service(
                service_id=str(uuid5(uuid5(NAMESPACE_URL, device_id), f"{protocol}:{port}")),
                device_id=device_id,
                protocol=protocol,
                port=port,
            )
            for protocol, ports_to_fill in (("tcp", profile_tcp_ports), ("udp", profile_udp_ports))
            for port in ports_to_fill
        ]
    else:
        services = list(parsed.values())
    return device, services
