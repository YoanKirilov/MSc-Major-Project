from uuid import uuid4

from app.profiling.history import compare_history
from app.schemas.scan import Device, ScanDocument, Service, TargetLedgerEntry


def report(day, ports):
    doc = ScanDocument(
        scan_id=str(uuid4()),
        created_at=f"2026-10-{day:02}T12:00:00Z",
        state="completed",
        phase="finished",
        target={"mode": "discover", "cidr": "192.168.56.0/24", "hosts": []},
        policy={
            "allowed_network": "192.168.56.0/24",
            "profile_id": "test-v1",
            "tcp_ports": [80, 443],
            "udp_ports": [],
        },
    )
    dev = Device(
        device_id=str(uuid4()), scan_id=doc.scan_id, ip="192.168.56.2", mac="aa:bb:cc:dd:ee:01"
    )
    doc.devices = [dev]
    doc.coverage.targets = [TargetLedgerEntry(ip=dev.ip, service_status="completed")]
    doc.services = [
        Service(service_id=str(uuid4()), device_id=dev.device_id, port=port, state="open")
        for port in ports
    ]
    return doc


def test_structured_differences_keep_dates_and_complete_evidence():
    previous, current = report(13, [80]), report(14, [443])
    compare_history(current, [previous])
    value = current.devices[0].comparison
    assert value.status == "available"
    assert value.source_created_at == previous.created_at
    assert value.added_count == value.not_observed_count == 1
    assert value.added[0].port == 443 and value.not_observed[0].port == 80
    assert (
        ScanDocument.model_validate(current.model_dump(mode="json")).devices[0].comparison == value
    )


def test_missing_identity_or_different_profile_never_becomes_no_changes():
    previous, current = report(13, [80]), report(14, [443])
    current.devices[0].mac = None
    compare_history(current, [previous])
    assert current.devices[0].comparison.status == "not_compared"
    current.devices[0].mac = previous.devices[0].mac
    current.policy["profile_id"] = "different"
    compare_history(current, [previous])
    assert current.devices[0].comparison.status == "not_compared"
    assert "different profiles" in current.devices[0].comparison.reason


def test_large_summary_is_bounded_without_losing_difference_totals():
    previous, current = report(13, []), report(14, list(range(1, 302)))
    compare_history(current, [previous])
    value = current.devices[0].comparison
    assert value.added_count == 301 and len(value.added) == 200
    assert len(current.services) == 301


def test_older_json_without_comparison_remains_readable():
    doc = report(13, [])
    raw = doc.model_dump(mode="json")
    del raw["devices"][0]["comparison"]
    assert ScanDocument.model_validate(raw).devices[0].comparison is None
