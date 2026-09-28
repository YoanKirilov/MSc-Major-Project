"""Pure interpretation and bounded presentation of previously collected device facts."""

import re
from datetime import datetime, timezone

from app.scanner.names import clean_name
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
    if value is None:
        return
    value = clean_name(value) if kind in {"upnp", "netbios"} else str(value)
    if not value:
        return
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
