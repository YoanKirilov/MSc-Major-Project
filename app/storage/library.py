"""Read-only library search across all reports, before pagination."""

import unicodedata
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, ip_network

from .annotations import AnnotationStore, ReportAnnotations
from .nicknames import NicknameDocument, NicknameStore


def words(value):
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    ).split()


def search_reports(
    store,
    *,
    q="",
    profile=None,
    state=None,
    after=None,
    before=None,
    offset=0,
    limit=20,
    scope=None,
    recent_devices=False,
):
    page = store._list_scans(source="live", offset=0, limit=2**31 - 1)
    annotations = AnnotationStore(store)
    nicknames = NicknameStore(store)
    warnings = set()
    try:
        saved_names = nicknames._load()
    except (OSError, ValueError):
        saved_names = NicknameDocument()
        warnings.add("Saved nicknames are unreadable; nickname matches may be missing.")
    results, devices, unreadable = [], [], []
    seen = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for item in page["items"]:
        if item["storage_status"] != "ok":
            unreadable.append(item["scan_id"])
            continue
        try:
            document = store.library_cache.load(store, item["scan_id"])
            if document.source != "live":
                continue
            if profile and document.policy.get("profile") != profile:
                continue
            if state and document.state != state:
                continue
            created = datetime.fromisoformat(document.created_at)
            if (after and created.date() < after) or (before and created.date() > before):
                continue
            if scope and document.policy.get("allowed_network") != scope:
                continue
            if recent_devices and (document.phase != "finished" or created < cutoff):
                continue
            _, names = nicknames._view(document, saved_names)
            if recent_devices:
                checks = {target.ip: target for target in document.coverage.targets}
                for device in document.devices:
                    if device.ip in seen or ip_address(device.ip) not in ip_network(scope):
                        continue
                    seen.add(device.ip)
                    devices.append(
                        {
                            "ip": device.ip,
                            "name": names.get(device.device_id)
                            or device.hostname
                            or "Unnamed device",
                            "observed_at": device.observed_at,
                            "report_created_at": document.created_at,
                            "scan_id": document.scan_id,
                            "check_status": checks[device.ip].service_status
                            if device.ip in checks
                            else "not_recorded",
                            "reachability": device.reachability,
                            "last_check": device_check_label(device, checks.get(device.ip)),
                        }
                    )
                continue
            try:
                annotation = annotations._load(document.scan_id)
            except (OSError, ValueError):
                annotation = ReportAnnotations()
                warnings.add("Some report titles are unreadable; title matches may be missing.")
            searchable = [annotation.title, document.created_at, document.scan_id]
            for device in document.devices:
                searchable.extend(
                    [
                        names.get(device.device_id, ""),
                        device.hostname or "",
                        device.ip,
                        device.vendor or "",
                        device.profile.category,
                    ]
                )
            searchable.extend(finding.title for finding in document.findings)
            haystack = " ".join(words(" ".join(searchable)))
            if not all(word in haystack for word in words(q)):
                continue
            results.append(
                {
                    **item,
                    "title": annotation.title,
                    "profile": document.policy.get("profile", "unknown"),
                    "target": document.target,
                }
            )
        except (OSError, ValueError, TypeError):
            unreadable.append(item["scan_id"])
    if unreadable:
        warnings.add(
            f"{len(unreadable)} saved report(s) could not be read. Their files are preserved; "
            "they are excluded from matches and device choices."
        )
    if recent_devices:
        return {
            "items": devices[:256],
            "total": len(devices),
            "days": 7,
            "warnings": sorted(warnings),
        }
    return {
        "items": results[offset : offset + limit],
        "total": len(results),
        "offset": offset,
        "limit": limit,
        "warnings": sorted(warnings),
        "unreadable_count": len(unreadable),
    }


def device_check_label(device, check):
    """Do not turn a completed check or an advertisement into proof of response."""
    if check and check.service_status in {"failed", "timed_out", "cancelled", "skipped"}:
        return {
            "failed": "Last device check did not finish",
            "timed_out": "Last device check timed out",
            "cancelled": "Last device check was cancelled",
            "skipped": "Last device check was not performed",
        }[check.service_status]
    if check and check.service_status == "completed":
        return "Last device check finished; not proof of safety"
    if device.reachability == "advertised":
        return "Advertised its presence; no completed device check recorded"
    if device.reachability == "observed":
        return "Seen on the network; no completed device check recorded"
    return "Address saved; response not confirmed"
