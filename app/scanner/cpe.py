"""Pure software-fingerprint validation; no provider, network or alias guessing."""

import re

from app.schemas.scan import Service


def _application_fields(value, *, version_required):
    if not isinstance(value, str):
        return None
    if value.startswith("cpe:/"):
        fields = value[5:].split(":")
        if not 3 <= len(fields) <= 7:
            return None
        fields = [part or "*" for part in fields] + ["*"] * (11 - len(fields))
    elif value.startswith("cpe:2.3:"):
        fields = value[8:].split(":")
        if len(fields) != 11:
            return None
    else:
        return None
    if fields[0] != "a" or any(part in {"*", "-"} for part in fields[1:3]):
        return None
    if (version_required or fields[3] != "*") and not any(char.isdigit() for char in fields[3]):
        return None
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}|\*", part) for part in fields):
        return None
    return fields


def application_cpe(value: str) -> str | None:
    """Accept the simple lossless versioned subset; never guess an identity."""
    fields = _application_fields(value, version_required=True)
    return "cpe:2.3:" + ":".join(fields) if fields else None


def product_cpe(value: str) -> str | None:
    """Same observed application vendor/product, with version/settings unverified."""
    fields = _application_fields(value, version_required=False)
    return "cpe:2.3:" + ":".join([*fields[:3], *(["*"] * 8)]) if fields else None


def service_product_cpe(service: Service) -> str | None:
    if service.state != "open" or service.detection_method != "probed":
        return None
    if service.nmap_confidence is None or service.nmap_confidence < 7:
        return None
    identities = {cpe for raw in service.cpes if (cpe := product_cpe(raw))}
    return next(iter(identities)) if len(identities) == 1 else None


def service_cpe(service: Service) -> str | None:
    if service.state != "open" or service.detection_method != "probed":
        return None
    if service.nmap_confidence is None or service.nmap_confidence < 7:
        return None
    identities = {cpe for raw in service.cpes if (cpe := application_cpe(raw))}
    return next(iter(identities)) if len(identities) == 1 else None
