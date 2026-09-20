from __future__ import annotations

from app.schemas.scan import Device, DeviceProfile, ExplanationRecord, Finding, FixedExplanation, Service


def make_telnet_scan() -> dict:
    device = Device(
        device_id="d2cc2a19-9fc9-5b9d-9c77-1f603d2ae911",
        scan_id="2d9aaddd-4c59-41dd-b5d8-256e5b49c811",
        ip="192.168.0.10",
        discovery_method="known_host",
        reachability="observed",
        reachability_evidence=["open_port_response"],
        profile=DeviceProfile(category="unknown", confidence="low", hints=[]),
        observed_at="2026-09-20T00:00:00Z",
    )
    service = Service(
        service_id="ee8c67ba-5744-5f2e-93de-df553d63a402",
        device_id=device.device_id,
        port=23,
        state="open",
        name="telnet",
        detection_method="probed",
        nmap_confidence=9,
        observed_at="2026-09-20T00:00:00Z",
    )
    finding = Finding(
        finding_id="0cb5b27b-3878-5d0c-8a35-8f8b684a30f8",
        device_id=device.device_id,
        service_id=service.service_id,
        rule_id="R01",
        rule_version="1.0.0",
        title="Telnet service identified",
        severity="high",
        confidence="medium",
        evidence=[{"field": "name", "value": "telnet"}, {"field": "state", "value": "open"}],
        limitations=["Only the observed selected port was probed."],
        fixed_explanation=FixedExplanation(
            meaning="Telnet is an unencrypted terminal service.",
            why_it_matters="It exposes management traffic without a verified encrypted transport.",
            recommended_steps=["Review whether the service is required.", "Use a secure management method instead."],
            how_to_check=["Check whether the service is enabled on the device.", "Confirm whether an encrypted alternative is available."],
        ),
        actions=[
            {"action_id": "review_service_need", "text": "Review whether the service is required.", "verification": "Check the device's allowed management configuration."},
            {"action_id": "use_secure_alternative", "text": "Use a supported secure management method instead.", "verification": "Verify that encrypted management is enabled."},
        ],
        references=[{"title": "Telnet guidance", "url": "https://example.com/telnet"}],
    )
    return {
        "device": device.model_dump(),
        "service": service.model_dump(),
        "finding": finding.model_dump(),
    }


def make_demo_scan() -> dict:
    return {
        "scan_id": "demo-scan-1",
        "source": "demo",
        "devices": [],
        "services": [],
        "findings": [],
    }
