"""Interpret bounded SMB negotiation evidence without guessing from port labels.

Nmap's two allowlisted scripts normally emit host results. Its SMB library chooses
open TCP 445 first, otherwise TCP 139 when UDP 137 is open or unknown. The fixed
Deep command passes no SMB port override. Direct port evidence, when present,
belongs only to that port; disagreeing evidence never produces a finding.

Sources: https://svn.nmap.org/nmap/nselib/smb.lua (get_port),
https://svn.nmap.org/nmap/scripts/smb-protocols.nse and smb2-security-mode.nse.
"""

from collections import Counter, defaultdict

from app.scanner.parser import SCRIPT_OUTPUT_LIMIT

SMB_DIALECTS = frozenset({"2.0.2", "2.1", "3.0", "3.0.2", "3.1.1"})
SMB1_LABELS = frozenset(
    {
        "NT LM 0.12",
        "NT LM 0.12 (SMBv1)",
        "NT LM 0.12 (SMBv1) [dangerous, but default]",
    }
)
SIGNING_STATES = {
    "Message signing enabled and required": ("enabled", True),
    "Message signing enabled but not required": ("enabled", False),
    "Message signing is disabled and not required!": ("disabled", False),
}


def _lines(script):
    if script.truncated or not script.output or len(script.output) > SCRIPT_OUTPUT_LIMIT:
        return None
    if any(not char.isprintable() and char not in "\t\r\n" for char in script.output):
        return None
    return [line.strip() for line in script.output.splitlines() if line.strip()]


def parse_protocols(script):
    """Accept complete recognised dialect rows, never a substring mentioning SMBv1."""
    lines = _lines(script)
    if not lines or lines[0] != "dialects:" or not 2 <= len(lines) <= 7:
        return None
    dialects = []
    for line in lines[1:]:
        value = "SMBv1" if line in SMB1_LABELS else line
        if value not in SMB_DIALECTS | {"SMBv1"} or value in dialects:
            return None
        dialects.append(value)
    return tuple(dialects)


def parse_signing(script):
    """Current NSE checks one negotiated version; do not generalise it to all versions."""
    lines = _lines(script)
    if not lines or len(lines) != 2 or not lines[0].endswith(":"):
        return None
    dialect = lines[0][:-1]
    state = SIGNING_STATES.get(lines[1])
    if dialect not in SMB_DIALECTS or state is None:
        return None
    return dialect, state[0], state[1]


def _endpoint(service, device):
    return (
        service.device_id == device.device_id
        and service.protocol == "tcp"
        and service.port in {139, 445}
        and service.state == "open"
        and service.tunnel is None
    )


def _default_endpoint(device, services):
    tcp = defaultdict(list)
    udp137 = []
    for service in services:
        if service.device_id != device.device_id:
            continue
        if service.protocol == "tcp" and service.port in {139, 445}:
            tcp[service.port].append(service)
        if service.protocol == "udp" and service.port == 137:
            udp137.append(service)
    # A duplicate port record cannot establish Nmap's selected endpoint.
    if len(tcp[445]) > 1:
        return None
    if tcp[445] and tcp[445][0].state == "open":
        candidate = tcp[445][0]
        return candidate if _endpoint(candidate, device) else None
    if len(tcp[139]) != 1 or len(udp137) > 1:
        return None
    if udp137 and udp137[0].state not in {"open", "open_filtered", "unknown"}:
        return None
    candidate = tcp[139][0]
    return candidate if _endpoint(candidate, device) else None


def _accepted_results(device, services, script_id, parse):
    host = [script for script in device.host_script_results if script.script_id == script_id]
    if len(host) > 1:
        return []
    host_result = parse(host[0]) if host else None
    if host and host_result is None:
        return []
    host_endpoint = _default_endpoint(device, services) if host else None
    if host and host_endpoint is None:
        return []
    endpoints = defaultdict(list)
    ports = defaultdict(list)
    for service in services:
        if service.device_id != device.device_id or service.protocol != "tcp":
            continue
        if service.port not in {139, 445}:
            continue
        ports[service.port].append(service)
        if _endpoint(service, device):
            endpoints[service.service_id].extend(
                script for script in service.script_results if script.script_id == script_id
            )
    results = []
    for service in services:
        if not _endpoint(service, device) or len(ports[service.port]) != 1:
            continue
        scripts = endpoints[service.service_id]
        attached_host = host_endpoint is not None and host_endpoint.service_id == service.service_id
        if len(scripts) > 1:
            continue
        direct_result = parse(scripts[0]) if scripts else None
        if scripts and direct_result is None:
            continue
        if attached_host and direct_result is not None and direct_result != host_result:
            continue
        parsed = host_result if attached_host else direct_result
        if parsed is not None:
            results.append(
                (
                    service,
                    parsed,
                    "host and port"
                    if attached_host and scripts
                    else "host"
                    if attached_host
                    else "port",
                )
            )
    return results


def configuration_observations(device, services):
    """Return only positive, endpoint-bound facts supporting the two configuration rules."""
    identifiers = Counter(
        service.service_id for service in services if service.device_id == device.device_id
    )
    if any(count > 1 for count in identifiers.values()):
        return []
    observations = []
    for service, dialects, origin in _accepted_results(
        device, services, "smb-protocols", parse_protocols
    ):
        if "SMBv1" in dialects:
            observations.append(
                (
                    "R08",
                    service,
                    [
                        ("script_id", "smb-protocols"),
                        ("script_scope", origin),
                        ("protocol", "tcp"),
                        ("port", service.port),
                        ("accepted_smb_version", "SMBv1"),
                        ("accepted_dialects", ", ".join(dialects)),
                        (
                            "endpoint_association",
                            "Nmap default SMB port selection"
                            if origin != "port"
                            else "Direct port result",
                        ),
                    ],
                )
            )
    for service, signing, origin in _accepted_results(
        device, services, "smb2-security-mode", parse_signing
    ):
        dialect, enabled, required = signing
        if required is False:
            observations.append(
                (
                    "R09",
                    service,
                    [
                        ("script_id", "smb2-security-mode"),
                        ("script_scope", origin),
                        ("protocol", "tcp"),
                        ("port", service.port),
                        ("negotiated_smb_version", dialect),
                        ("message_signing", enabled),
                        ("message_signing_required", False),
                        (
                            "endpoint_association",
                            "Nmap default SMB port selection"
                            if origin != "port"
                            else "Direct port result",
                        ),
                    ],
                )
            )
    return observations
