from tests.fixtures.fixtures import make_telnet_scan
from app.risk.engine import evaluate_device
from app.schemas.scan import Device, Service


def test_probed_telnet_creates_high_finding():
    fixture = make_telnet_scan()
    device = Device.model_validate(fixture["device"])
    service = Service.model_validate(fixture["service"])
    findings = evaluate_device(device, [service])
    assert len(findings) == 1
    assert findings[0].rule_id == "R01"
    assert findings[0].severity == "high"
    assert {item.field for item in findings[0].evidence} >= {"state", "name", "detection_method"}


def test_table_only_telnet_does_not_create_high_finding():
    fixture = make_telnet_scan()
    device = Device.model_validate(fixture["device"])
    service = Service.model_validate({**fixture["service"], "detection_method": "table", "nmap_confidence": None})
    findings = evaluate_device(device, [service])
    assert findings == []


def test_closed_telnet_is_not_a_finding():
    fixture = make_telnet_scan()
    device = Device.model_validate(fixture["device"])
    service = Service.model_validate({**fixture["service"], "state": "closed"})
    assert evaluate_device(device, [service]) == []
