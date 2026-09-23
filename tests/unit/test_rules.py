import pytest

from tests.fixtures.fixtures import make_telnet_scan
from app.risk.engine import evaluate_device
from app.risk.catalogue import RULE_CATALOGUE
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


@pytest.mark.parametrize("name, rule_id", [
    ("telnet", "R01"), ("ftp", "R02"), ("http", "R03"),
    ("ms-wbt-server", "R04"), ("microsoft-ds", "R05"), ("mqtt", "R06"),
])
def test_service_rule_mapping(name, rule_id):
    fixture = make_telnet_scan()
    device = Device.model_validate(fixture["device"])
    service = Service.model_validate({**fixture["service"], "name": name})
    assert [finding.rule_id for finding in evaluate_device(device, [service])] == [rule_id]


@pytest.mark.parametrize("name", ["telnet", "ftp", "http"])
def test_encrypted_services_do_not_trigger_cleartext_rules(name):
    fixture = make_telnet_scan()
    device = Device.model_validate(fixture["device"])
    service = Service.model_validate({**fixture["service"], "name": name, "tunnel": "ssl"})
    assert evaluate_device(device, [service]) == []


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


def test_all_rules_have_specific_plain_language_explanations():
    for rule in RULE_CATALOGUE.values():
        assert rule["meaning"] and rule["why_it_matters"]
        assert "This indicates a service is reachable" not in rule["why_it_matters"]
        assert len(rule["meaning"].split()) <= 35
        assert len(rule["why_it_matters"].split()) <= 35


def test_identified_services_without_specific_rules_are_not_called_unknown():
    fixture = make_telnet_scan()
    device = Device.model_validate(fixture["device"])
    for name in ("domain", "snmp", "rtsp"):
        service = Service.model_validate({**fixture["service"], "name": name, "nmap_confidence": 10})
        finding = evaluate_device(device, [service])[0]
        assert finding.rule_id == "R07"
        assert "No specific security assessment" in finding.fixed_explanation.meaning
        assert "could not identify" not in finding.fixed_explanation.meaning
        assert any(item.field == "name" and item.value == name for item in finding.evidence)
