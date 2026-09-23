from __future__ import annotations

from app.schemas.scan import Device, Service

HINTS = {
    "camera": {"hostname": ["camera", "ipcam"], "service": ["rtsp"]},
    "printer": {"hostname": ["printer"], "service": ["ipp"]},
    "router": {"hostname": ["router", "gateway"], "service": []},
}


def classify_device(device: Device, services: list[Service] | None = None):
    hints = []
    text = " ".join(filter(None, [device.hostname, device.vendor])).lower()
    service_names = {service.name.lower() for service in (services or []) if service.name}
    for category, config in HINTS.items():
        for token in config["hostname"]:
            if token in text:
                hints.append({"source": "hostname", "category": category, "token": token})
        for token in config["service"]:
            if token in service_names:
                hints.append({"source": "service", "category": category, "token": token})
    if not hints:
        return {"category": "unknown", "confidence": "low", "hints": [], "conflict": False}
    by_category = {}
    for hint in hints:
        by_category.setdefault(hint["category"], set()).add(hint["source"])
    if len(by_category) == 1:
        category, sources = next(iter(by_category.items()))
        if len(sources) >= 2:
            return {"category": category, "confidence": "medium", "hints": hints, "conflict": False}
        return {"category": "unknown", "confidence": "low", "hints": hints, "conflict": False}
    return {"category": "unknown", "confidence": "low", "hints": hints, "conflict": True}
