from uuid import uuid4

import pytest
from app.explanations.report import report_input
from app.profiling.history import earlier_observations
from app.schemas.scan import Device, ScanDocument, TargetLedgerEntry


def report(day):
    return ScanDocument(
        scan_id=str(uuid4()),
        created_at=f"2026-10-{day:02}T12:00:00Z",
        phase="finished",
        state="completed",
        target={"mode": "discover", "cidr": "192.168.56.0/24", "hosts": []},
        policy={
            "profile": "light",
            "profile_id": "test-v1",
            "allowed_network": "192.168.56.0/24",
            "tcp_ports": [80],
            "udp_ports": [],
        },
        coverage={"discovery_complete": True},
    )


def add_device(doc, n, status="completed", **changes):
    device = Device(
        device_id=str(uuid4()),
        scan_id=doc.scan_id,
        ip=f"192.168.56.{n}",
        mac=f"aa:bb:cc:dd:ee:{n:02x}",
        hostname=f"Device {n}",
        hostname_source="reverse_dns",
    )
    for key, value in changes.items():
        setattr(device, key, value)
    doc.devices.append(device)
    doc.coverage.targets.append(
        TargetLedgerEntry(ip=device.ip, discovery_status="observed", service_status=status)
    )
    return device


def test_separate_view_of_unmatched_completed_observations_preserves_facts():
    previous, current = report(6), report(7)
    add_device(previous, 10)
    add_device(previous, 11, "failed")
    before = current.model_dump()
    result = earlier_observations(current, [previous])
    assert result.status == "available" and len(result.items) == 1
    assert result.items[0].last_ip == "192.168.56.10"
    assert result.source_scan_id == previous.scan_id
    assert "not proof" in result.reason and "unfinished" in result.reason
    assert current.model_dump() == before
    current.earlier_observations = result
    _, ai_input = report_input(current)
    assert "Device 10" not in str(ai_input) and "192.168.56.10" not in str(ai_input)


@pytest.mark.parametrize(
    "case",
    [
        "no_mac",
        "zero_mac",
        "duplicate_mac",
        "same_mac_new_ip",
        "same_ip_no_mac",
        "discovery_only_current_ip",
    ],
)
def test_identity_uncertainty_does_not_become_an_absence_claim(case):
    previous, current = report(6), report(7)
    old = add_device(previous, 10)
    if case == "no_mac":
        old.mac = None
    elif case == "zero_mac":
        old.mac = "00:00:00:00:00:00"
    elif case == "duplicate_mac":
        add_device(previous, 11, mac=old.mac)
    elif case == "same_mac_new_ip":
        add_device(current, 20, mac=old.mac)
    elif case == "same_ip_no_mac":
        add_device(current, 10, mac=None)
    else:
        current.coverage.targets = [
            TargetLedgerEntry(ip=old.ip, discovery_status="observed", service_status="failed")
        ]
    assert earlier_observations(current, [previous]).items == []


@pytest.mark.parametrize(
    "case",
    [
        "deep",
        "known_hosts",
        "scope",
        "cidr",
        "profile",
        "ports",
        "current_incomplete",
        "previous_incomplete",
        "unfinished_report",
        "old",
        "future",
        "unrecorded_profile",
    ],
)
def test_comparison_requires_recent_compatible_discovery(case):
    previous, current = report(6), report(7)
    add_device(previous, 10)
    if case == "deep":
        current.policy["profile"] = "deep-tcp-v1"
    elif case == "known_hosts":
        current.target = {"mode": "known_hosts", "hosts": ["192.168.56.20"]}
    elif case == "scope":
        previous.policy["allowed_network"] = "192.168.0.0/24"
    elif case == "cidr":
        previous.target["cidr"] = "192.168.56.0/25"
    elif case == "profile":
        previous.policy["profile_id"] = "other"
    elif case == "ports":
        previous.policy["tcp_ports"] = [80, 443]
    elif case == "current_incomplete":
        current.coverage.discovery_complete = False
    elif case == "previous_incomplete":
        previous.coverage.discovery_complete = False
    elif case == "unfinished_report":
        previous.phase = "service_scan"
    elif case == "old":
        previous.created_at = "2026-09-01T12:00:00Z"
    elif case == "future":
        previous.created_at = "2026-10-08T12:00:00Z"
    else:
        current.policy.pop("profile_id")
    result = earlier_observations(current, [previous])
    assert result.status == "not_compared" and not result.items


def test_view_bounded_uses_newest_compatible_report_and_does_not_choose_conflicting_name():
    previous, current = report(6), report(7)
    for n in range(1, 61):
        add_device(previous, n)
    previous.devices[0].hostname_conflict = True
    result = earlier_observations(current, [report(5), previous])
    assert len(result.items) == 50 and result.omitted_count == 10
    assert result.items[0].reported_name is None
    assert result.source_scan_id == previous.scan_id
