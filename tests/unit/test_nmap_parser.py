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


def summary_xml(ports):
    return (
        '<nmaprun><host><status state="up" reason="user-set"/>'
        '<address addr="192.168.56.10" addrtype="ipv4"/>'
        f'<ports>{ports}</ports></host><runstats><finished exit="success"/></runstats></nmaprun>'
    ).encode()


def test_closed_port_summaries_preserve_protocol_states_and_reachability():
    xml = summary_xml(
        '<extraports state="closed" count="15">'
        '<extrareasons reason="conn-refused" count="12" proto="tcp" '
        'ports="21-23,80,443,445,554,1883,3389,5900,8080,8443"/>'
        '<extrareasons reason="port-unreach" count="3" proto="udp" ports="53,161,1900"/>'
        "</extraports>"
    )
    device, services = parse_host(xml, "192.168.56.10", "summary-test")
    assert device.reachability == "observed"
    assert "closed_port_response" in device.reachability_evidence
    assert len(services) == 15 and all(s.state == "closed" for s in services)
    assert all(s.name is None and s.detection_method == "unknown" for s in services)
    assert {s.state_reason for s in services if s.protocol == "udp"} == {"port-unreach"}


def test_mixed_summary_states_do_not_cross_protocols_or_replace_explicit_services():
    xml = summary_xml(
        '<port protocol="tcp" portid="80"><state state="open" reason="syn-ack"/>'
        '<service name="http" method="probed" conf="10"/></port>'
        '<extraports state="closed" count="1">'
        '<extrareasons reason="conn-refused" count="1" proto="tcp" ports="53"/>'
        '</extraports><extraports state="open|filtered" count="1">'
        '<extrareasons reason="no-response" count="1" proto="udp" ports="53"/>'
        "</extraports>"
    )
    _, services = parse_host(
        xml, "192.168.56.10", "summary-test", profile_tcp_ports=[53, 80], profile_udp_ports=[53]
    )
    by_port = {(s.protocol, s.port): s for s in services}
    assert by_port["tcp", 53].state == "closed"
    assert by_port["udp", 53].state == "open_filtered"
    assert by_port["tcp", 80].name == "http"


@pytest.mark.parametrize(
    "attributes",
    [
        'count="1"',
        'count="1" ports="80"',
        'count="1" proto="tcp"',
        'count="2" proto="tcp" ports="80"',
        'count="1" proto="tcp" ports="80,bad"',
        'count="1" proto="tcp" ports="65536"',
        'count="1" proto="tcp" ports="81-80"',
        'count="1" proto="tcp" ports="9999"',
    ],
)
def test_ambiguous_malformed_or_out_of_profile_summary_does_not_invent_evidence(attributes):
    xml = summary_xml(
        f'<extraports state="closed" count="1"><extrareasons {attributes}/></extraports>'
    )
    device, services = parse_host(xml, "192.168.56.10", "summary-test")
    assert device.reachability == "unconfirmed"
    assert all(s.state == "unknown" for s in services)


def test_filtered_summary_does_not_establish_a_response():
    xml = summary_xml(
        '<extraports state="filtered" count="1">'
        '<extrareasons reason="no-response" count="1" proto="tcp" ports="80"/></extraports>'
    )
    device, services = parse_host(xml, "192.168.56.10", "summary-test")
    assert device.reachability == "unconfirmed"
    assert next(s for s in services if s.port == 80).state == "filtered"


def test_deep_closed_summary_confirms_response_without_expanding_65535_services():
    xml = summary_xml(
        '<extraports state="closed" count="65535">'
        '<extrareasons reason="conn-refused" count="65535" proto="tcp" ports="1-65535"/>'
        "</extraports>"
    )
    device, services = parse_host(
        xml,
        "192.168.56.10",
        "summary-test",
        profile_tcp_ports=range(1, 65536),
        fill_unknown=False,
    )
    assert device.reachability == "observed"
    assert services == []


def test_conflicting_explicit_and_summary_states_are_rejected():
    xml = summary_xml(
        '<port protocol="tcp" portid="80"><state state="open"/></port>'
        '<extraports state="closed" count="1">'
        '<extrareasons count="1" proto="tcp" ports="80"/></extraports>'
    )
    with pytest.raises(ValueError, match="conflicting summarized"):
        parse_host(xml, "192.168.56.10", "summary-test")


def test_host_failure_diagnostics_do_not_expose_unreviewed_text():
    from app.scanner.parser import host_failure_detail

    assert "exactly one device record" in host_failure_detail(
        ValueError("host XML must contain exactly one host")
    )
    assert "did not match" in host_failure_detail(
        ValueError("host XML contains an unexpected target")
    )
    assert host_failure_detail(ValueError("<script>untrusted device output</script>")) == (
        "The returned scan data could not be validated."
    )
