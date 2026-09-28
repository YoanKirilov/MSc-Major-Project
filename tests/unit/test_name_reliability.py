import pytest
from app.profiling.history import compare_history
from app.scanner.names import add_mdns_names
from app.schemas.scan import Device, DiscoveryObservation
from tests.unit.test_device_details import document


def test_mdns_uses_friendly_name_instead_of_generated_instance_id():
    dev = Device(device_id="d", scan_id="s", ip="192.168.0.2")
    add_mdns_names(
        dev,
        DiscoveryObservation(
            ip=dev.ip,
            advertised_name="cast-123456",
            service_type="_googlecast._tcp.local.",
            properties={"fn": "Living room TV"},
        ),
    )
    assert dev.hostname == "Living room TV" and not dev.hostname_conflict


def test_mdns_hostname_fallback_and_audio_prefix():
    dev = Device(device_id="d", scan_id="s", ip="192.168.0.2")
    add_mdns_names(
        dev,
        DiscoveryObservation(
            ip=dev.ip,
            advertised_name="",
            service_type="_http._tcp.local.",
            hostname="printer.local.",
        ),
    )
    assert dev.hostname == "printer.local."
    dev.hostname = None
    dev.name_candidates = []
    add_mdns_names(
        dev,
        DiscoveryObservation(
            ip=dev.ip, advertised_name="AABBCCDDEEFF@Room speaker", service_type="_raop._tcp.local."
        ),
    )
    assert dev.hostname == "Room speaker"


def pair():
    current = document(created="2026-09-25T22:00:00Z")
    old = document(created="2026-09-25T21:00:00Z")
    for doc in (current, old):
        doc.devices[0].mac = "aa:bb:cc:dd:ee:ff"
    old.devices[0].hostname = "Room TV"
    old.devices[0].hostname_source = "mdns"
    old.devices[0].hostname_observed_at = old.created_at
    return current, old


def test_recent_name_is_restored_as_historical_without_changing_evidence():
    current, old = pair()
    old_json = old.model_dump_json()
    compare_history(current, [old])
    dev = current.devices[0]
    assert dev.hostname == "Room TV" and dev.hostname_source == "saved_report"
    assert dev.hostname_observed_at == old.created_at and dev.hostname_confidence == "low"
    assert dev.reachability == "unconfirmed" and not current.observations
    assert dev.name_candidates[0]["report_id"] == old.scan_id
    assert old.model_dump_json() == old_json


@pytest.mark.parametrize("reason", ["ip_reused", "scope", "stale", "chain", "duplicate", "future"])
def test_history_does_not_invent_current_name_matches(reason):
    current, old = pair()
    if reason == "ip_reused":
        current.devices[0].mac = "aa:bb:cc:dd:ee:01"
    elif reason == "scope":
        old.policy["allowed_network"] = "192.168.1.0/24"
    elif reason == "stale":
        old.devices[0].hostname_observed_at = "2026-09-01T21:00:00Z"
    elif reason == "chain":
        old.devices[0].hostname_source = "saved_report"
    elif reason == "duplicate":
        old.devices.append(old.devices[0].model_copy(deep=True))
    elif reason == "future":
        old.devices[0].hostname_observed_at = "2026-09-26T21:00:00Z"
    compare_history(current, [old])
    assert current.devices[0].hostname is None


def test_current_name_wins_and_historical_conflicts_stay_visible():
    current, old = pair()
    current.devices[0].hostname = "Fresh name"
    compare_history(current, [old])
    assert current.devices[0].hostname == "Fresh name"
    current.devices[0].hostname = None
    old.devices[0].hostname_conflict = True
    old.devices[0].name_candidates = [
        {"name": "Other label", "source": "mdns", "observed_at": old.created_at}
    ]
    compare_history(current, [old])
    assert current.devices[0].hostname_conflict is True
    assert any(c["name"] == "Other label" for c in current.devices[0].name_candidates)
