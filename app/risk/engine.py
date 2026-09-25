from __future__ import annotations

from uuid import UUID, uuid5

from app.schemas.scan import EvidenceItem, Finding, FixedExplanation

from .catalogue import RULE_CATALOGUE

SERVICE_RULES = {
    "telnet": "R01",
    "ftp": "R02",
    "http": "R03",
    "ms-wbt-server": "R04",
    "microsoft-ds": "R05",
    "mqtt": "R06",
}


def service_name_key(name: str | None) -> str | None:
    if name is None:
        return None
    return name.strip().lower()


def evaluate_device(device, services, catalogue=None):
    catalogue = catalogue or RULE_CATALOGUE
    results = []
    for service in services:
        if service.state != "open":
            continue
        if service.detection_method != "probed":
            continue
        name = service_name_key(service.name)
        if name is None:
            continue
        if service.nmap_confidence is not None and service.nmap_confidence < 7:
            continue
        if service.tunnel == "ssl":
            if name in {"telnet", "ftp", "http"}:
                continue
        matched = SERVICE_RULES.get(name)
        if matched is None:
            if name == "ssh" and service.nmap_confidence and service.nmap_confidence >= 7:
                continue
            matched = "R07"
        rule = catalogue[matched]
        evidence = [
            EvidenceItem(field="protocol", value=service.protocol),
            EvidenceItem(field="state", value=service.state),
            EvidenceItem(field="name", value=service.name),
            EvidenceItem(field="detection_method", value=service.detection_method),
            EvidenceItem(field="nmap_confidence", value=service.nmap_confidence),
        ]
        if service.tunnel is not None:
            evidence.append(EvidenceItem(field="tunnel", value=service.tunnel))
        finding = Finding(
            finding_id=str(uuid5(UUID(service.service_id), f"{matched}:{rule['version']}")),
            device_id=device.device_id,
            service_id=service.service_id,
            rule_id=matched,
            rule_version=rule["version"],
            title=rule["title"],
            severity=rule["severity"],
            confidence=rule["confidence"],
            evidence=evidence,
            limitations=rule["limitations"],
            fixed_explanation=FixedExplanation(
                meaning=rule["meaning"],
                why_it_matters=rule["why_it_matters"],
                recommended_steps=[action["text"] for action in rule["actions"]],
                how_to_check=[action["verification"] for action in rule["actions"]],
            ),
            actions=[
                {
                    "action_id": action["action_id"],
                    "text": action["text"],
                    "verification": action["verification"],
                }
                for action in rule["actions"]
            ],
            references=rule["references"],
        )
        results.append(finding)
    return results
