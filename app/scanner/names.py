"""Device labels with provenance; names never establish reachability."""

import re

from app.schemas.scan import Device


def clean_name(value) -> str | None:
    if not isinstance(value, str):
        return None
    value = "".join(char for char in value if char.isprintable()).strip()[:255]
    return value if value and value not in {"*", "(none)"} else None


def normalise_mac(value) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.replace("-", ":").lower()
    return value if re.fullmatch(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", value) else None


def add_mdns_names(device, observation) -> None:
    """Prefer explicit friendly names; fall back to the announced hostname."""
    friendly = clean_name(observation.properties.get("fn"))
    instance = clean_name(observation.advertised_name)
    # RAOP instances may prefix the readable label with a hardware identifier.
    if instance and observation.service_type.startswith("_raop."):
        instance = re.sub(r"^[0-9a-fA-F]{12}@", "", instance)
    primary = friendly or instance or clean_name(observation.hostname)
    if primary:
        add_name(device, primary, "mdns", observation.observed_at)


def add_name(device: Device, name, source: str, observed_at: str, **metadata) -> None:
    name = clean_name(name)
    if not name:
        return
    candidate = {"name": name, "source": source, "observed_at": observed_at, **metadata}
    if candidate not in device.name_candidates:
        device.name_candidates.append(candidate)
    names = {item["name"].lower().rstrip(".") for item in device.name_candidates}
    device.hostname_conflict = len(names) > 1
    sources = {item["source"] for item in device.name_candidates}
    device.hostname_confidence = (
        "medium" if len(sources) > 1 and not device.hostname_conflict else "low"
    )
    if not device.hostname:
        device.hostname = name
        device.hostname_source = source
        device.hostname_observed_at = observed_at
