from pathlib import Path

import pytest
from app.scanner.parser import parse_host

FIXTURE = Path(__file__).parents[1] / "fixtures" / "nmap_host.xml"


def test_host_parser_returns_fixed_service_slots_and_evidence():
    device, services = parse_host(
        FIXTURE.read_bytes(), "192.168.56.10", "55555555-5555-4555-8555-555555555555"
    )
    assert device.hostname == "camera-office"
    assert device.host_script_results[0].script_id == "host-check"
    assert device.reachability == "observed"
    assert len(services) == 15
    telnet = next(service for service in services if service.port == 23)
    assert telnet.detection_method == "probed"
    assert telnet.nmap_confidence == 9
    assert telnet.name == "telnet"
    assert telnet.script_results[0].output == "Safe service evidence"
    snmp = next(
        service for service in services if service.protocol == "udp" and service.port == 161
    )
    assert snmp.name == "snmp"
    assert snmp.nmap_confidence == 8


def test_host_parser_rejects_unexpected_target():
    with pytest.raises(ValueError, match="unexpected target"):
        parse_host(FIXTURE.read_bytes(), "192.168.56.11", "55555555-5555-4555-8555-555555555555")


def test_host_parser_rejects_malformed_xml():
    with pytest.raises(ValueError, match="malformed"):
        parse_host(b"<nmaprun>", "192.168.56.10", "55555555-5555-4555-8555-555555555555")


@pytest.mark.parametrize("length", [500, 1500])
def test_script_output_has_explicit_1024_character_limit(length):
    xml = FIXTURE.read_bytes().replace(b"Safe service evidence", b"x" * length)
    _, services = parse_host(xml, "192.168.56.10", "55555555-5555-4555-8555-555555555555")
    evidence = next(item for item in services if item.port == 23).script_results[0]
    assert len(evidence.output) == min(length, 1024)
    assert evidence.truncated is (length > 1024)


def test_nmap_mac_and_vendor_are_preserved():
    xml = FIXTURE.read_bytes().replace(
        b"<host>", b'<host><address addrtype="mac" addr="00:11:22:33:44:55" vendor="Example"/>'
    )
    device, _ = parse_host(xml, "192.168.56.10", "55555555-5555-4555-8555-555555555555")
    assert device.mac == "00:11:22:33:44:55" and device.vendor == "Example"
