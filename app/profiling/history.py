"""Conservative comparisons against a bounded set of previous local reports."""

from datetime import datetime, timedelta

from app.scanner.names import add_name, normalise_mac
from app.scanner.observations import detail


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
    try:
        now = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
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
        try:
            age = now - datetime.fromisoformat(observed.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
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
    previous = sorted(
        [
            p
            for p in previous
            if p.source == "live"
            and current.policy.get("allowed_network")
            and p.scan_id != current.scan_id
            and p.created_at < current.created_at
            and p.policy.get("allowed_network") == current.policy.get("allowed_network")
            and p.phase == "finished"
        ],
        key=lambda p: p.created_at,
        reverse=True,
    )
    for device in current.devices:
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
            message = (
                "This IP address appeared before, but device identity could not be matched."
                if address_seen
                else "No matching device was found in the recent reports checked. "
                "This does not mean the device is new to your network."
            )
            detail(
                device, "history", "Earlier observations", message, "Saved reports", "not_checked"
            )
            continue
        last, old = matches[0]
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
            detail(
                device,
                "history",
                "Service comparison",
                "Not compared: profiles differ, port selections are missing, "
                "or a device check was incomplete.",
                "Saved reports",
                "not_checked",
            )
            continue
        before, after = ports(last, old), ports(current, device)
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
