import pytest

from app.risk.guidance import guidance_status, refresh_guidance
from app.schemas.scan import Device, Finding, ScanDocument, Service
from tests.fixtures.fixtures import make_telnet_scan


def legacy_document():
    fixture = make_telnet_scan()
    return ScanDocument(
        scan_id="2d9aaddd-4c59-41dd-b5d8-256e5b49c811",
        state="completed", phase="finished",
        target={"mode": "known_hosts", "hosts": ["192.168.0.10"], "cidr": None},
        devices=[Device.model_validate(fixture["device"])],
        services=[Service.model_validate(fixture["service"])],
        findings=[Finding.model_validate(fixture["finding"])],
    )


def test_refresh_preserves_evidence_ratings_dates_and_archives_previous_guidance():
    document = legacy_document()
    before = document.model_dump(mode="json")
    assert guidance_status(document)["refresh_available"]
    updated = refresh_guidance(document)
    assert document.model_dump(mode="json") == before
    assert updated.devices == document.devices
    assert updated.services == document.services
    for key in ("finding_id", "severity", "confidence", "evidence", "created_at"):
        assert getattr(updated.findings[0], key) == getattr(document.findings[0], key)
    assert updated.guidance_history[0].findings == document.findings
    assert updated.guidance_updated_at
    assert updated.findings[0].rule_version == "1.1.0"
    assert not guidance_status(updated)["refresh_available"]
    assert refresh_guidance(updated) == updated


def test_refresh_needs_supporting_observations_and_completed_work():
    document = legacy_document()
    document.services = []
    assert not guidance_status(document)["refresh_available"]
    assert guidance_status(document)["outdated_findings"] == 1
    assert refresh_guidance(document) == document
    document.phase = "analysis"
    with pytest.raises(RuntimeError, match="SCAN_NOT_READY"):
        refresh_guidance(document)
