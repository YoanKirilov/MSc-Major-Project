"""Conservative comparisons against a bounded set of previous local reports."""

from app.scanner.details import detail
from app.scanner.names import normalise_mac


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
                "Not compared: profiles differ or a device check was incomplete.",
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
