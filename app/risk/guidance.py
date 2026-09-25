"""Explicitly update guidance from saved observations, without network requests."""

from app.schemas.common import iso_z, utc_now
from app.schemas.scan import GuidanceSnapshot, ScanDocument

from .catalogue import RULE_CATALOGUE, RULESET_VERSION
from .engine import evaluate_device

GUIDANCE_FIELDS = (
    "title",
    "rule_version",
    "limitations",
    "fixed_explanation",
    "actions",
    "references",
)


def guidance_updates(document: ScanDocument) -> dict:
    available = {}
    for device in document.devices:
        services = [
            service for service in document.services if service.device_id == device.device_id
        ]
        for finding in evaluate_device(device, services):
            available[(finding.device_id, finding.service_id, finding.rule_id)] = finding
    updates = {}
    for saved in document.findings:
        latest = available.get((saved.device_id, saved.service_id, saved.rule_id))
        # Wording refresh must not silently revise a risk assessment or its evidence.
        if latest is None or (latest.severity, latest.confidence) != (
            saved.severity,
            saved.confidence,
        ):
            continue
        if any(getattr(saved, key) != getattr(latest, key) for key in GUIDANCE_FIELDS):
            updates[saved.finding_id] = latest
    return updates


def guidance_status(document: ScanDocument) -> dict:
    outdated = sum(
        finding.rule_id in RULE_CATALOGUE
        and finding.rule_version != RULE_CATALOGUE[finding.rule_id]["version"]
        for finding in document.findings
    )
    return {
        "current_rules_version": RULESET_VERSION,
        "outdated_findings": outdated,
        "refresh_available": bool(guidance_updates(document)),
        "updated_at": document.guidance_updated_at,
    }


def refresh_guidance(document: ScanDocument) -> ScanDocument:
    if (
        document.state not in {"completed", "partial", "failed", "cancelled"}
        or document.phase != "finished"
    ):
        raise RuntimeError("SCAN_NOT_READY")
    updates = guidance_updates(document)
    if not updates:
        return document
    now = iso_z(utc_now())
    snapshot = GuidanceSnapshot(
        saved_at=now,
        versions=dict(document.versions),
        findings=[finding.model_copy(deep=True) for finding in document.findings],
        explanations=[record.model_copy(deep=True) for record in document.explanations],
    )
    findings = [
        finding.model_copy(
            update={key: getattr(updates[finding.finding_id], key) for key in GUIDANCE_FIELDS}
        )
        if finding.finding_id in updates
        else finding
        for finding in document.findings
    ]
    versions = dict(document.versions)
    if all(
        f.rule_id in RULE_CATALOGUE and f.rule_version == RULE_CATALOGUE[f.rule_id]["version"]
        for f in findings
    ):
        versions["rules"] = RULESET_VERSION
    return document.model_copy(
        update={
            "findings": findings,
            "explanations": [],
            "report_explanation": None,
            "analysis_status": "not_started",
            "analysis_error": None,
            "versions": versions,
            "guidance_history": [*document.guidance_history, snapshot],
            "guidance_updated_at": now,
        }
    )
