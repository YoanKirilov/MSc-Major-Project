from app.schemas.scan import Device, Finding, ScanDocument, Service
from tests.fixtures.fixtures import make_telnet_scan


def test_telnet_fixture_round_trip():
    fixture = make_telnet_scan()
    device = Device.model_validate(fixture["device"])
    service = Service.model_validate(fixture["service"])
    finding = Finding.model_validate(fixture["finding"])
    assert device.ip == "192.168.0.10"
    assert service.port == 23
    assert finding.rule_id == "R01"
    assert finding.fixed_explanation.meaning


def test_invalid_scan_document_rejected():
    try:
        ScanDocument.model_validate(
            {
                "scan_id": "bad",
                "source": "live",
                "devices": [],
                "services": [],
                "findings": [],
                "target": {"mode": "discover", "hosts": ["1.1.1.1"], "cidr": None},
                "coverage": {"targets": []},
            }
        )
    except Exception:
        return
    raise AssertionError("Expected validation failure for invalid scan document")


def test_service_port_rejected_outside_profile():
    try:
        Service(
            service_id="x",
            device_id="d",
            port=0,
            state="closed",
        )
    except Exception:
        return
    raise AssertionError("Unsupported port should be rejected")
