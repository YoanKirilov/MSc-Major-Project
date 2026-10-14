"""Read-only, intentionally small sharing projection of a saved live report."""

from __future__ import annotations

import asyncio
import ipaddress
import re
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.api.dependencies import require_session
from app.explanations.presentation import plain_finding, plain_report
from app.explanations.service import PROMPT_VERSION
from app.schemas.common import iso_z, utc_now
from app.storage.annotations import ReportAnnotations
from app.storage.nicknames import NicknameDocument, NicknameStore

router = APIRouter(prefix="/api")

PRIVACY_NOTICE = (
    "Device names and network addresses are removed by default, including recognised identifiers "
    "in explanatory text. Dates, feature details and your wording can still identify a household. "
    "Review this preview before sharing; it is not a guarantee of anonymity."
)
REVIEW_STATUS_NOTE = (
    "Checked records your own review. It does not confirm a fix or change the original "
    "observed priority. A new comparable check is needed to assess a change."
)
MAX_PRIVATE_TOKENS = 2048
MAX_PRIVATE_TOKEN_CHARS = 64 * 1024


class PrivatePreviewTooLarge(ValueError):
    """A private preview must not silently discard identifiers to meet its budget."""


def _read_optional(store, path, model):
    """Do not invoke sidecar recovery: exporting must never rewrite saved data."""
    if not path.exists() and not path.is_symlink():
        companions = (path.with_suffix(".previous.json"), path.with_suffix(".recovery.json"))
        if not any(item.exists() or item.is_symlink() for item in companions):
            return model(), True
        return model(), False
    try:
        return model.model_validate(store._read_json(path)), True
    except (OSError, ValueError):
        return model(), False


def _sidecars(store, document):
    annotations, notes_available = _read_optional(
        store, store._scan_dir(document.scan_id) / "annotations.json", ReportAnnotations
    )
    nicknames, names_available = _read_optional(
        store, store.data_root / "nicknames.json", NicknameDocument
    )
    # _view with an explicit validated snapshot only reads identity anchors.
    _, names = NicknameStore(store)._view(document, nicknames)
    return annotations, notes_available, names, names_available


def _identifier_tokens(document, names, annotations):
    values = set()
    characters = 0

    def add(*items):
        nonlocal characters
        for item in items:
            if not isinstance(item, str) or not item.strip():
                continue
            value = item.strip()
            if value in values:
                continue
            if (
                len(values) >= MAX_PRIVATE_TOKENS
                or characters + len(value) > MAX_PRIVATE_TOKEN_CHARS
            ):
                raise PrivatePreviewTooLarge("The private preview exceeds its identifier budget")
            values.add(value)
            characters += len(value)

    add(*names.values())
    for device in document.devices:
        add(device.ip, device.hostname, device.mac)
        for candidate in device.name_candidates:
            add(*(candidate.get(key) for key in ("name", "hostname", "value")))
        add(*(detail.value for detail in device.details))
    for target in document.coverage.targets:
        add(target.ip, target.discovery_hostname, target.discovery_mac)
    for item in document.observations:
        add(item.ip, item.hostname, item.advertised_name)
        add(*item.properties.values())
    if document.earlier_observations:
        for item in document.earlier_observations.items:
            add(item.last_ip, item.reported_name)
    for refresh in annotations.name_refreshes:
        for name in refresh.names:
            add(*(name.get(key) for key in ("name", "hostname", "value")))
    return sorted(values, key=len, reverse=True)


def _redactor(document, names, annotations, include_identifiers):
    if include_identifiers:
        return lambda value: str(value) if value is not None else ""
    tokens = _identifier_tokens(document, names, annotations)
    known = (
        re.compile(
            r"(?<![\w-])(?:" + "|".join(re.escape(value) for value in tokens) + r")(?![\w-])",
            re.IGNORECASE,
        )
        if tokens
        else None
    )
    ipv4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?(?![\w.])")
    mac = re.compile(r"(?<![\w])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![\w])", re.IGNORECASE)
    ipv6 = re.compile(
        r"(?<![\w])(?:[0-9a-f]{0,4}:){2,}[0-9a-f:]{0,39}"
        r"(?:%[\w.-]+)?(?:/\d{1,3})?(?![\w])",
        re.IGNORECASE,
    )
    # URL/domain text can contain an address that was not a discovery candidate.
    url = re.compile(r"\b(?:https?|ftp)://[^\s<>\"']+", re.IGNORECASE)
    domain = re.compile(r"\b[\w-]+(?:\.[\w-]+)+\.?\b", re.IGNORECASE)

    def redact(value):
        text = str(value) if value is not None else ""
        text = url.sub("[address omitted]", text)
        text = mac.sub("[address omitted]", text)
        text = ipv4.sub("[address omitted]", text)

        def redact_ipv6(match):
            candidate = match.group(0)
            try:
                ipaddress.ip_interface(candidate)
            except ValueError:
                return candidate
            return "[address omitted]"

        text = ipv6.sub(redact_ipv6, text)
        if known:
            text = known.sub("[identifier omitted]", text)
        return domain.sub("[address omitted]", text)

    return redact


def _content(value, redact):
    return {
        "meaning": redact(value["meaning"]),
        "why_it_matters": redact(value["why_it_matters"]),
        "recommended_steps": [redact(line) for line in value["recommended_steps"]],
        "how_to_check": [redact(line) for line in value["how_to_check"]],
    }


def _wording(plain, record, redact, *, overview=False):
    usable = (
        record is not None
        and record.status == "ready"
        and record.source == "ai"
        and record.content is not None
        and record.prompt_version == PROMPT_VERSION
    )
    fields = list(record.ai_fields) if usable else []
    if usable and not fields and not overview:
        fields = ["meaning", "why_it_matters"]
    content = dict(plain["content"])
    if usable:
        accepted = record.content.model_dump()
        for field in ("meaning", "why_it_matters", "recommended_steps", "how_to_check"):
            if field in fields:
                content[field] = accepted[field]
    title = plain.get("title", "Your scan results explained")
    limitations = plain["limitations"]
    if "title" in fields and record.display_title:
        title = record.display_title
    if "limitations" in fields and record.display_limitations is not None:
        limitations = record.display_limitations
    return {
        "title": redact(title),
        "content": _content(content, redact),
        "limitations": [redact(line) for line in limitations],
        "provenance": {
            "source": "ai_assisted" if usable else "reviewed_guidance",
            "ai_fields": fields,
            "provider": redact(record.provider) if usable else None,
            "model": redact(record.model) if usable else None,
            "prompt_version": record.prompt_version if usable else None,
            "completed_at": record.completed_at if usable else None,
            "unaccepted_field_count": len(record.rejected_fields) if record else 0,
            "older_ai_wording_hidden": bool(
                record and record.prompt_version and record.prompt_version != PROMPT_VERSION
            ),
        },
    }


def _port_selection(values, *, tcp=False):
    if not isinstance(values, (list, tuple)):
        return []
    return [
        value
        for value in values
        if (type(value) is int and 1 <= value <= 65535) or (tcp and value == "all-tcp")
    ]


def build_share_report(
    document,
    *,
    include_identifiers=False,
    include_notes=False,
    annotations=None,
    notes_available=True,
    names=None,
    names_available=True,
):
    """Allowlist fields; never export raw XML, scripts, banners, CPEs or provider payloads."""
    annotations = annotations or ReportAnnotations()
    names = names or {}
    redact = _redactor(document, names, annotations, include_identifiers)
    deep = document.policy.get("profile") == "deep-tcp-v1"
    profile = "Deep" if deep else "Light"
    labels = {
        device.device_id: f"Device {index}" for index, device in enumerate(document.devices, 1)
    }
    features = {
        service.service_id: f"Feature {index}" for index, service in enumerate(document.services, 1)
    }
    services_by_device = {}
    for service in document.services:
        services_by_device.setdefault(service.device_id, []).append(service)
    statuses = {(item.finding_id, item.action_id): item for item in annotations.action_checks}
    records = {record.finding_id: record for record in document.explanations}
    devices = []
    for device in document.devices:
        item = {
            "label": labels[device.device_id],
            "observed_at": device.observed_at,
            "reachability": device.reachability,
            "features": [
                {
                    "label": features[service.service_id],
                    "name": redact(service.name or "Unidentified feature"),
                    "protocol": service.protocol,
                    "port": service.port,
                    "state": service.state,
                    "detection_method": service.detection_method,
                    "observed_at": service.observed_at,
                }
                for service in services_by_device.get(device.device_id, [])
            ],
        }
        if include_identifiers:
            item["identifiers"] = {
                "ip": device.ip,
                "hostname": device.hostname,
                "mac": device.mac,
                "nickname": names.get(device.device_id),
            }
        devices.append(item)

    findings = []
    priority = {"high": 0, "medium": 1, "low": 2, "informational": 3}
    for index, finding in enumerate(
        sorted(document.findings, key=lambda item: priority[item.severity]), 1
    ):
        wording = _wording(plain_finding(finding), records.get(finding.finding_id), redact)
        actions = []
        for position, action in enumerate(finding.actions):
            check = statuses.get((finding.finding_id, action.action_id))
            steps = wording["content"]["recommended_steps"]
            verification = wording["content"]["how_to_check"]
            actions.append(
                {
                    "label": f"Task {position + 1}",
                    "step": steps[position] if position < len(steps) else redact(action.text),
                    "verification": verification[position]
                    if position < len(verification)
                    else redact(action.verification),
                    "review_status": (check.status if check else "to_check")
                    if notes_available
                    else "unavailable",
                    "review_updated_at": check.updated_at if check and notes_available else None,
                }
            )
        findings.append(
            {
                **wording,
                "label": f"Review item {index}",
                "device_label": labels.get(finding.device_id, "Device not recorded"),
                "feature_label": features.get(finding.service_id, "Feature not recorded"),
                "severity": finding.severity,
                "confidence": finding.confidence,
                "observed_at": finding.created_at,
                "fixed_title": redact(finding.title),
                "fixed_explanation": _content(finding.fixed_explanation.model_dump(), redact),
                "fixed_limitations": [redact(line) for line in finding.limitations],
                "actions": actions,
            }
        )

    coverage = document.coverage
    addresses = {device.ip: labels[device.device_id] for device in document.devices}
    discovery = document.target.get("mode") == "discover"
    selected = {value for value in document.target.get("hosts", []) if isinstance(value, str)}
    listed_targets = []
    unlisted_targets = []
    for target in coverage.targets:
        listed = target.discovery_status == "observed" if discovery else target.ip in selected
        (listed_targets if listed else unlisted_targets).append(target)
    target_label = "Discovered target" if discovery else "Selected target"
    result = {
        "schema_version": 1,
        "title": redact(annotations.title)
        if include_notes and annotations.title
        else f"{profile} scan report",
        "generated_at": iso_z(utc_now()),
        "created_at": document.created_at,
        "started_at": document.started_at,
        "finished_at": document.finished_at,
        "state": document.state,
        "scan_outcome": document.scan_outcome,
        "profile_label": profile,
        "privacy": {
            "include_identifiers": include_identifiers,
            "include_notes": include_notes,
            "notice": PRIVACY_NOTICE,
        },
        "scope": {
            "mode": "discovered" if discovery else "selected",
            "tcp_ports": _port_selection(
                document.policy.get("tcp_ports", document.policy.get("ports")), tcp=True
            ),
            "udp_ports": _port_selection(document.policy.get("udp_ports")),
        },
        "coverage": {
            "candidate_count": coverage.candidate_count,
            "discovered_count": coverage.discovered_count,
            "service_attempted_count": coverage.service_attempted_count,
            "service_completed_count": coverage.service_completed_count,
            "service_failed_count": coverage.service_failed_count,
            "service_skipped_count": coverage.service_skipped_count,
            "unfinished_device_count": document.unfinished_device_count,
            "discovery_complete": coverage.discovery_complete,
            "service_stage_complete": coverage.service_stage_complete,
            "unlisted_target_count": len(unlisted_targets),
            "unlisted_not_observed_count": sum(
                target.discovery_status != "observed" for target in unlisted_targets
            ),
            "unlisted_skipped_count": sum(
                target.service_status == "skipped" for target in unlisted_targets
            ),
            "unlisted_not_scheduled_count": sum(
                target.service_status == "not_scheduled" for target in unlisted_targets
            ),
            "targets": [
                {
                    "label": addresses.get(target.ip, f"{target_label} {index}"),
                    "discovery_status": target.discovery_status,
                    "service_status": target.service_status,
                    "reason_code": redact(target.reason_code),
                    **({"ip": target.ip} if include_identifiers else {}),
                }
                for index, target in enumerate(listed_targets, 1)
            ],
        },
        "overview": _wording(
            plain_report(document), document.report_explanation, redact, overview=True
        ),
        "devices": devices,
        "findings": findings,
        "warnings": [
            {"code": redact(item.get("code")), "message": redact(item.get("message"))}
            for item in document.warnings
        ],
        "errors": [
            {"code": redact(item.get("code")), "message": redact(item.get("message"))}
            for item in document.errors
        ],
        "versions": {
            key: redact(document.versions.get(key)) for key in ("app", "rules", "prompt", "nmap")
        },
        "review_status_note": REVIEW_STATUS_NOTE,
        "annotations_available": notes_available,
        "nicknames_available": names_available,
    }
    if include_notes:
        result["notes"] = {
            "title": redact(annotations.title),
            "identification_notes": [
                {
                    "device_label": labels.get(str(refresh.device_id), "Device not recorded"),
                    "checked_at": refresh.checked_at,
                    "notes": [redact(line) for line in refresh.notes],
                }
                for refresh in annotations.name_refreshes
            ],
        }
    return result


@router.get("/live-scans/{scan_id}/share")
async def share_report(
    request: Request,
    response: Response,
    scan_id: str,
    include_identifiers: Annotated[Literal["true", "false"], Query()] = "false",
    include_notes: Annotated[Literal["true", "false"], Query()] = "false",
):
    require_session(request)
    response.headers["Cache-Control"] = "no-store"
    try:
        document = await request.app.state.store.load_scan(scan_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(404, "Saved live report not found") from exc
    except OSError as exc:
        raise HTTPException(503, "The saved report could not be read. Try again shortly.") from exc
    if document.source != "live":
        raise HTTPException(404, "Saved live report not found")
    if document.phase != "finished" or document.state in {"queued", "running"}:
        raise HTTPException(409, "Wait for this report to finish before sharing it")
    annotations, notes_available, names, names_available = await asyncio.to_thread(
        _sidecars, request.app.state.store, document
    )
    try:
        return build_share_report(
            document,
            include_identifiers=include_identifiers == "true",
            include_notes=include_notes == "true",
            annotations=annotations,
            notes_available=notes_available,
            names=names,
            names_available=names_available,
        )
    except PrivatePreviewTooLarge as exc:
        raise HTTPException(
            413,
            "This report contains too many distinct identifiers for a private preview. "
            "Choose a smaller saved report, or explicitly include identifiers and review "
            "the resulting information before sharing.",
        ) from exc
