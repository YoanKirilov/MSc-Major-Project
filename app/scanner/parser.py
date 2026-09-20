from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from defusedxml import ElementTree

from app.schemas.scan import Device, Service
from app.scanner.commands import PORTS


def _text(element, attribute: str) -> str | None:
    value = element.attrib.get(attribute)
    if value is None:
        return None
    cleaned = "".join(char for char in value if char >= " " or char in "\t\n\r")
    return cleaned[:255] or None


def _require_completed(root):
    if root.tag != "nmaprun":
        raise ValueError("unexpected XML root")
    runstats = root.find("runstats")
    finished = runstats is not None and runstats.find("finished") is not None
    if not finished:
        raise ValueError("scan XML is incomplete")


def parse_discovery(xml_bytes: bytes, candidates: tuple[str, ...]) -> tuple[str, ...]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except Exception as exc:
        raise ValueError("malformed discovery XML") from exc
    _require_completed(root)
    allowed = set(candidates)
    observed = []
    for host in root.findall("host"):
        address = host.find("address[@addrtype='ipv4']")
        if address is None or address.attrib.get("addr") not in allowed:
            raise ValueError("discovery XML contains an unexpected target")
        status = host.find("status")
        if status is not None and status.attrib.get("state") == "up":
            observed.append(address.attrib["addr"])
    return tuple(sorted(set(observed)))


def parse_host(xml_bytes: bytes, expected_ip: str, scan_id: str, discovery_method: str = "known_host") -> tuple[Device, list[Service]]:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except Exception as exc:
        raise ValueError("malformed host XML") from exc
    _require_completed(root)
    hosts = root.findall("host")
    if len(hosts) != 1:
        raise ValueError("host XML must contain exactly one host")
    host = hosts[0]
    address = host.find("address[@addrtype='ipv4']")
    if address is None or address.attrib.get("addr") != expected_ip:
        raise ValueError("host XML contains an unexpected target")

    device_id = str(uuid5(uuid5(NAMESPACE_URL, scan_id), f"device:{expected_ip}"))
    hostnames = host.find("hostnames/hostname")
    device = Device(
        device_id=device_id,
        scan_id=scan_id,
        ip=expected_ip,
        hostname=_text(hostnames, "name") if hostnames is not None else None,
        discovery_method=discovery_method,
        reachability="unconfirmed",
        reachability_evidence=[],
    )
    parsed: dict[int, Service] = {}
    ports = host.find("ports")
    if ports is not None:
        for port_node in ports.findall("port"):
            if port_node.attrib.get("protocol") != "tcp":
                continue
            try:
                port = int(port_node.attrib["portid"])
            except (KeyError, ValueError):
                continue
            if port not in PORTS:
                continue
            state_node = port_node.find("state")
            state_value = state_node.attrib.get("state", "unknown") if state_node is not None else "unknown"
            state_value = {"open|filtered": "open_filtered", "closed|filtered": "closed_filtered"}.get(state_value, state_value)
            if state_value not in {"open", "closed", "filtered", "open_filtered", "closed_filtered", "unfiltered", "unknown"}:
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
            service_id = str(uuid5(uuid5(NAMESPACE_URL, device_id), f"tcp:{port}"))
            parsed_service = Service(
                service_id=service_id,
                device_id=device_id,
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
            )
            if port in parsed and parsed[port].model_dump(exclude={"observed_at"}) != parsed_service.model_dump(exclude={"observed_at"}):
                raise ValueError("conflicting duplicate port record")
            parsed[port] = parsed_service
            if state_value in {"open", "closed", "unfiltered"}:
                device.reachability = "observed"
                device.reachability_evidence = ["open_port_response" if state_value == "open" else "closed_port_response"]
    services = [parsed.get(port) or Service(service_id=str(uuid5(uuid5(NAMESPACE_URL, device_id), f"tcp:{port}")), device_id=device_id, port=port) for port in PORTS]
    return device, services
