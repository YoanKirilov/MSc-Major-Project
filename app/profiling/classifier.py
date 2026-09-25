from __future__ import annotations

from app.schemas.scan import Device, Service

HINTS = {
    "camera": {"hostname": ["camera", "ipcam"], "service": ["rtsp"]},
    "printer": {"hostname": ["printer"], "service": ["ipp"]},
    "router": {"hostname": ["router", "gateway"], "service": []},
    "computer": {"hostname": ["macbook", "desktop", "laptop"], "service": []},
    "media": {"hostname": ["bravia", "television", "smart-tv"], "service": []},
}


def classify_device(device: Device, services: list[Service] | None = None):
    if device.hostname_conflict:
        return {"category": "unknown", "confidence": "low", "hints": [], "conflict": True}
    hints = []
    text = (device.hostname or "").lower()
    name_source = (
        device.hostname_source if device.hostname_source in {"mdns", "upnp"} else "hostname"
    )
    service_names = {
        service.name.lower()
        for service in (services or [])
        if service.name and service.state == "open"
    }
    for category, config in HINTS.items():
        for token in config["hostname"]:
            if token in text:
                hints.append({"source": name_source, "category": category, "token": token})
        for token in config["service"]:
            if token in service_names:
                hints.append({"source": "service", "category": category, "token": token})
    for item in device.details:
        value = item.value.lower()
        if item.kind == "mdns" and item.label == "Advertised feature":
            category = (
                "printer"
                if "printing" in value
                else "media"
                if any(word in value for word in ("media", "audio streaming"))
                else None
            )
            if category:
                hints.append({"source": "mdns", "category": category, "token": item.value})
        elif item.kind in {"mdns", "upnp"} and item.status == "advertised":
            for token, category in (
                ("macbook", "computer"),
                ("mediarenderer", "media"),
                ("bravia", "media"),
                ("printer", "printer"),
                ("internetgatewaydevice", "router"),
            ):
                if token in value:
                    hints.append({"source": item.kind, "category": category, "token": token})
    if not hints:
        return {"category": "unknown", "confidence": "low", "hints": [], "conflict": False}
    by_category = {}
    for hint in hints:
        by_category.setdefault(hint["category"], set()).add(hint["source"])
    if len(by_category) == 1:
        category, sources = next(iter(by_category.items()))
        if len(sources) >= 2 or sources & {"mdns", "upnp"}:
            return {
                "category": category,
                "confidence": "medium" if len(sources) >= 2 else "low",
                "hints": hints,
                "conflict": False,
            }
        return {"category": "unknown", "confidence": "low", "hints": hints, "conflict": False}
    return {"category": "unknown", "confidence": "low", "hints": hints, "conflict": True}
