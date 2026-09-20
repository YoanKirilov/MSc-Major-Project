from __future__ import annotations

PORTS = (21, 22, 23, 80, 443, 445, 554, 1883, 3389, 5900, 8080, 8443)
PROFILE_ID = "tcp12-v1"


def discovery_command(nmap_path: str, cidr: str) -> list[str]:
    return [nmap_path, "-sn", "-n", "-oX", "-", cidr]


def host_command(nmap_path: str, ip: str) -> list[str]:
    return [
        nmap_path,
        "-n",
        "-Pn",
        "-sT",
        "-sV",
        "--version-light",
        "--max-retries",
        "1",
        "--host-timeout",
        "25s",
        "-p",
        ",".join(str(port) for port in PORTS),
        "-oX",
        "-",
        ip,
    ]
