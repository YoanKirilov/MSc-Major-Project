"""Conservative comparisons against a bounded set of previous local reports."""

from datetime import timedelta
from uuid import UUID

from app.scanner.names import add_name, normalise_mac
from app.scanner.observations import detail
from app.schemas.common import observation_time
from app.schemas.scan import ComparedService, DeviceComparison, EarlierDevice, EarlierObservations


def earlier_observations(current, previous):
    """Earlier observations, not an absence verdict or an identity match by IP."""
    unavailable = EarlierObservations(
        reason="This view needs two recent Light network-discovery scans of the same range "
        "with matching checks and finished discovery."
    )
    if (
        current.source != "live"
        or current.policy.get("profile") != "light"
        or current.target.get("mode") != "discover"
        or not current.target.get("cidr")
        or not current.policy.get("allowed_network")
        or not current.coverage.discovery_complete
        or current.policy.get("profile_id") is None
        or any(not isinstance(current.policy.get(key), list) for key in ("tcp_ports", "udp_ports"))
    ):
        return unavailable
    now = observation_time(current.created_at)
    if now is None:
        return unavailable
    candidates = [
        (observed, doc)
        for doc in previous
        if doc.source == "live"
        and doc.phase == "finished"
        and doc.scan_id != current.scan_id
        and doc.target == current.target
        and doc.coverage.discovery_complete
        and all(
            doc.policy.get(key) == current.policy.get(key)
            for key in ("allowed_network", "profile", "profile_id", "tcp_ports", "udp_ports")
        )
        and (observed := observation_time(doc.created_at)) is not None
        and timedelta(0) <= now - observed <= timedelta(days=7)
    ]
    if not candidates:
        return unavailable
    _, last = max(candidates, key=lambda entry: (entry[0], entry[1].scan_id))
    current_macs = {normalise_mac(device.mac) for device in current.devices}
    observed_ips = {device.ip for device in current.devices} | {
        target.ip for target in current.coverage.targets if target.discovery_status == "observed"
    }
    items = []
    for device in last.devices:
        mac = normalise_mac(device.mac)
        if (
            not mac
            or mac == "00:00:00:00:00:00"
            or mac in current_macs
            or device.ip in observed_ips
            or not complete(last, device.ip)
            or sum(normalise_mac(other.mac) == mac for other in last.devices) != 1
        ):
            continue
        items.append(
            EarlierDevice(
                last_ip=device.ip,
                reported_name=None if device.hostname_conflict else device.hostname,
                name_source=device.hostname_source,
                observed_at=device.observed_at or last.created_at,
            )
        )
    items.sort(key=lambda item: tuple(map(int, item.last_ip.split("."))))
    return EarlierObservations(
        status="available",
        source_scan_id=last.scan_id,
        items=items[:50],
        omitted_count=max(0, len(items) - 50),
        reason="These earlier completed device observations were not matched this time. "
        "Devices may be asleep, disconnected, or using changed addresses. This is not "
        "proof they were removed, repaired or unsafe; older unfinished checks are excluded.",
    )


def complete(doc, ip):
    return any(t.ip == ip and t.service_status == "completed" for t in doc.coverage.targets)


def ports(doc, dev):
    return {
        (s.protocol, s.port)
        for s in doc.services
        if s.device_id == dev.device_id and s.state == "open"
    }


def format_ports(values):
    labels = [f"{proto.upper()} {port}" for proto, port in sorted(values)]
    return (
        ", ".join(labels[:12]) + (f" (+{len(labels) - 12} more)" if len(labels) > 12 else "")
    ) or "none"


def restore_previous_name(device, matches, created_at):
    """Display a recent direct observation as historical, never a current reply."""
    if device.hostname:
        return
    now = observation_time(created_at)
    if now is None:
        return
    for report, old in matches:
        if not old.hostname or old.hostname_source not in {
            "nmap",
            "nmap_discovery",
            "reverse_dns",
            "mdns",
            "upnp",
            "netbios",
            "pihole_dhcp",
            "pihole_network",
        }:
            continue  # Do not repeatedly extend the lifetime of a historical name.
        observed = old.hostname_observed_at or old.observed_at or report.created_at
        instant = observation_time(observed)
        if instant is None:
            continue
        age = now - instant
        if not timedelta(0) <= age <= timedelta(days=7):
            continue
        add_name(
            device,
            old.hostname,
            "saved_report",
            observed,
            report_id=report.scan_id,
            original_source=old.hostname_source,
        )
        device.hostname_conflict = old.hostname_conflict
        if old.hostname_conflict:
            for candidate in old.name_candidates:
                add_name(
                    device,
                    candidate.get("name"),
                    "saved_report",
                    observed,
                    report_id=report.scan_id,
                    original_source=candidate.get("source", "unknown"),
                )
            device.hostname_conflict = True
        device.hostname_confidence = "low"
        return


def compare_history(current, previous):
    now = observation_time(current.created_at)
    previous = sorted(
        [
            (observed, p)
            for p in previous
            if p.source == "live"
            and current.policy.get("allowed_network")
            and p.scan_id != current.scan_id
            and now is not None
            and (observed := observation_time(p.created_at)) is not None
            and observed < now
            and p.policy.get("allowed_network") == current.policy.get("allowed_network")
            and p.phase == "finished"
        ],
        key=lambda entry: (entry[0], entry[1].scan_id),
        reverse=True,
    )
    previous = [doc for _, doc in previous]
    for device in current.devices:
        device.comparison = DeviceComparison(
            current_created_at=current.created_at,
            reason=(
                "No reliably matched earlier check is available; this is not proof of no changes."
            ),
        )
        mac = normalise_mac(device.mac)
        matches = [
            (p, old)
            for p in previous
            for old in p.devices
            if mac and mac != "00:00:00:00:00:00" and normalise_mac(old.mac) == mac
        ]
        # Duplicate MAC observations are ambiguous, not an identity match.
        if any(sum(normalise_mac(d.mac) == mac for d in p.devices) > 1 for p, _ in matches) or (
            mac and sum(normalise_mac(d.mac) == mac for d in current.devices) > 1
        ):
            device.comparison.reason = "Repeated adapter addresses prevent a reliable comparison."
            detail(
                device,
                "history",
                "Earlier observations",
                "A repeated network-adapter address prevents a reliable comparison.",
                "Saved reports",
                "not_checked",
            )
            continue
        if not matches:
            address_seen = any(d.ip == device.ip for p in previous for d in p.devices)
            if not previous:
                message = (
                    "No earlier finished report for this network was available "
                    "among the recent reports checked."
                )
            elif not mac or mac == "00:00:00:00:00:00":
                message = (
                    "No usable network-adapter address was recorded to match this device reliably."
                )
            elif address_seen:
                message = (
                    "This IP address appeared before, but device identity could not be matched."
                )
            else:
                message = (
                    "No matching network-adapter address was found in the recent reports checked."
                )
            message += (
                " This does not mean the device is new to your network; "
                "an IP address alone is not a reliable identity."
            )
            detail(
                device, "history", "Earlier observations", message, "Saved reports", "not_checked"
            )
            continue
        last, old = matches[0]
        device.comparison.source_scan_id = UUID(last.scan_id)
        device.comparison.source_created_at = last.created_at
        restore_previous_name(device, matches, current.created_at)
        detail(
            device,
            "history",
            "Previously seen",
            f"Same network-adapter address in report {last.scan_id} ({last.created_at}). "
            "Addresses can be changed or copied; this is not verified identity.",
            "Saved reports",
            "inferred",
        )
        comparable = (
            current.policy.get("profile_id") is not None
            and all(
                isinstance(doc.policy.get(key), list)
                for doc in (current, last)
                for key in ("tcp_ports", "udp_ports")
            )
            and all(
                current.policy.get(k) == last.policy.get(k)
                for k in ("profile_id", "tcp_ports", "udp_ports")
            )
            and complete(current, device.ip)
            and complete(last, old.ip)
        )
        if not comparable:
            reasons = []
            if not complete(current, device.ip) or not complete(last, old.ip):
                reasons.append("one or both device checks did not finish")
            if current.policy.get("profile_id") is None or any(
                not isinstance(doc.policy.get(key), list)
                for doc in (current, last)
                for key in ("tcp_ports", "udp_ports")
            ):
                reasons.append("the scan profile or selected ports were not recorded")
            elif any(
                current.policy.get(key) != last.policy.get(key)
                for key in ("profile_id", "tcp_ports", "udp_ports")
            ):
                reasons.append("the scans used different profiles or port selections")
            device.comparison.reason = "Not compared: " + "; ".join(reasons) + "."
            detail(
                device,
                "history",
                "Service comparison",
                "Not compared: "
                + "; ".join(reasons)
                + ". No conclusion about service changes is available.",
                "Saved reports",
                "not_checked",
            )
            continue
        before, after = ports(last, old), ports(current, device)
        device.comparison.status = "available"
        device.comparison.reason = (
            "Same recorded adapter address and compatible completed checks; "
            "not verified physical identity, an attack verdict or proof of a fix."
        )
        device.comparison.added_count = len(after - before)
        device.comparison.not_observed_count = len(before - after)
        device.comparison.added = [
            ComparedService(protocol=proto, port=port)
            for proto, port in sorted(after - before)[:200]
        ]
        device.comparison.not_observed = [
            ComparedService(protocol=proto, port=port)
            for proto, port in sorted(before - after)[:200]
        ]
        detail(
            device,
            "history",
            "Service comparison",
            f"Newly observed open: {format_ports(after - before)}. "
            f"Previously open, not observed open now: {format_ports(before - after)}. "
            "A difference is not proof of an attack or a permanent change.",
            "Saved reports",
            "inferred",
        )
