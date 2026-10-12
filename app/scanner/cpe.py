"""Pure software-fingerprint validation; no provider, network or alias guessing."""

import re

from app.schemas.scan import Service


def application_cpe(value: str) -> str | None:
    """Accept the simple lossless subset; never broaden escaped/packed CPE names."""
    if not isinstance(value, str):
        return None
    if value.startswith("cpe:/"):
        fields = value[5:].split(":")
        if not 4 <= len(fields) <= 7:
            return None
        fields = [part or "*" for part in fields] + ["*"] * (11 - len(fields))
    elif value.startswith("cpe:2.3:"):
        fields = value[8:].split(":")
        if len(fields) != 11:
            return None
    else:
        return None
    if fields[0] != "a" or any(part in {"*", "-"} for part in fields[1:4]):
        return None
    if not any(char.isdigit() for char in fields[3]):
        return None
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}|\*", part) for part in fields):
        return None
    return "cpe:2.3:" + ":".join(fields)


def service_cpe(service: Service) -> str | None:
    if service.state != "open" or service.detection_method != "probed":
        return None
    if service.nmap_confidence is None or service.nmap_confidence < 7:
        return None
    identities = {cpe for raw in service.cpes if (cpe := application_cpe(raw))}
    return next(iter(identities)) if len(identities) == 1 else None
