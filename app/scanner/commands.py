from __future__ import annotations

PORTS = (21, 22, 23, 80, 443, 445, 554, 1883, 3389, 5900, 8080, 8443)
UDP_PORTS = (53, 161, 1900)
DEEP_UDP_PORTS = (
    53,
    67,
    68,
    69,
    123,
    137,
    138,
    161,
    162,
    500,
    514,
    1194,
    1434,
    1701,
    1812,
    1813,
    1900,
    2049,
    3478,
    4500,
    5060,
    5353,
    5683,
    11211,
    51820,
)
PROFILE_ID = "tcp12-udp3-v5"
LIGHT_PROFILE = "light"
DEEP_PROFILE = "deep-tcp-v1"

LIGHT_SAFE_SCRIPTS = "dns-recursion,snmp-info,upnp-info,http-title,http-headers,ssl-cert"
DEEP_SAFE_SCRIPTS = (
    "dns-recursion,ntp-info,snmp-info,upnp-info,http-title,http-headers,"
    "http-methods,ssl-cert,ssh-hostkey,rdp-enum-encryption,smb-os-discovery"
)


def _port_selection(tcp_ports: tuple[int, ...], udp_ports: tuple[int, ...]) -> str:
    tcp = ",".join(str(port) for port in tcp_ports)
    udp = ",".join(str(port) for port in udp_ports)
    return f"T:{tcp},U:{udp}"


def _deep_port_selection() -> str:
    return f"T:1-65535,U:{','.join(str(port) for port in DEEP_UDP_PORTS)}"


def discovery_command(nmap_path: str, cidr: str, interface: str | None = None) -> list[str]:
    command = [nmap_path, "-sn", "-n"]
    if interface:
        command.extend(["-e", interface])
    return [*command, "-oX", "-", cidr]


def host_command(
    nmap_path: str,
    ip: str,
    profile: str = LIGHT_PROFILE,
    interface: str | None = None,
) -> list[str]:
    interface_args = ["-e", interface] if interface else []
    if profile == DEEP_PROFILE:
        return [
            nmap_path,
            "-n",
            "-Pn",
            "-sT",
            "-sU",
            "-sV",
            "--version-all",
            *interface_args,
            "--reason",
            "--script",
            DEEP_SAFE_SCRIPTS,
            "--script-timeout",
            "30s",
            "--max-retries",
            "2",
            "--host-timeout",
            "900s",
            "-p",
            _deep_port_selection(),
            "-oX",
            "-",
            ip,
        ]
    return [
        nmap_path,
        "-n",
        "-Pn",
        "-sT",
        "-sU",
        "-sV",
        "--version-light",
        *interface_args,
        "--reason",
        "--script",
        LIGHT_SAFE_SCRIPTS,
        "--script-timeout",
        "15s",
        "--max-retries",
        "1",
        "--host-timeout",
        "180s",
        "-p",
        _port_selection(PORTS, UDP_PORTS),
        "-oX",
        "-",
        ip,
    ]
