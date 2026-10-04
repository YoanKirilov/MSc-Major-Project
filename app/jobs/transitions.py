"""Pure saved-report transitions; no network, process or storage operations."""

from app.schemas.common import iso_z, utc_now
from app.schemas.scan import ExplanationRecord


def close_unfinished(current, reason: str, *, cancelled: bool = False):
    coverage = current.coverage.model_copy(deep=True)
    for target in coverage.targets:
        eligible = (
            current.target.get("mode") == "known_hosts" or target.discovery_status == "observed"
        )
        if eligible and target.service_status in {"pending", "running"}:
            queued = reason == "scan_queue_expired" and target.attempts == 0
            target.service_status = "cancelled" if cancelled else "skipped" if queued else "failed"
            target.reason_code = reason
            if queued:
                coverage.service_skipped_count += 1
            elif not cancelled:
                coverage.service_failed_count += 1
    coverage.service_stage_complete = False
    return current.model_copy(update={"coverage": coverage})


def interrupted_document(current):
    if current.phase == "analysis" and current.analysis_status == "running":
        return current.model_copy(
            update={
                "state": current.scan_outcome or "failed",
                "phase": "finished",
                "analysis_status": "failed",
                "analysis_error": "process_restarted",
                "analysis_progress": current.analysis_progress.model_copy(
                    update={"state": "finished", "active": 0}
                )
                if current.analysis_progress
                else None,
                "finished_at": iso_z(utc_now()),
            }
        )
    if current.phase == "analysis" and current.state in {"completed", "partial"}:
        finished_at = iso_z(utc_now())
        existing = {record.finding_id: record for record in current.explanations}
        explanations = []
        for finding in current.findings:
            record = existing.get(finding.finding_id)
            if record is not None and record.status == "ready":
                explanations.append(record)
            else:
                explanations.append(
                    ExplanationRecord(
                        finding_id=finding.finding_id,
                        status="fallback",
                        source="fixed",
                        completed_at=finished_at,
                        fallback_reason="process_restarted",
                        content=finding.fixed_explanation,
                    )
                )
        return current.model_copy(
            update={
                "phase": "finished",
                "explanations": explanations,
                "warnings": [
                    *current.warnings,
                    {
                        "code": "AI_EXPLANATION_INTERRUPTED",
                        "message": (
                            "Plain-language AI wording was interrupted; fixed guidance is shown."
                        ),
                    },
                ],
            }
        )
    coverage = current.coverage.model_copy(deep=True)
    for target in coverage.targets:
        if target.service_status in {"pending", "running"}:
            target.service_status = "cancelled"
            target.reason_code = "process_restarted"
    coverage.service_stage_complete = False
    state = "partial" if current.devices else "failed"
    return current.model_copy(
        update={
            "state": state,
            "phase": "finished",
            "finished_at": iso_z(utc_now()),
            "coverage": coverage,
            "errors": [
                *current.errors,
                {
                    "code": "SCAN_INTERRUPTED",
                    "message": "The application stopped before this scan completed.",
                    "device_id": None,
                },
            ],
        }
    )


def mark_host_failure(current, ip, status, code, *, cancelled=False, detail=None):
    coverage = current.coverage.model_copy(deep=True)
    if not cancelled:
        coverage.service_failed_count += 1
    for target in coverage.targets:
        if target.ip == ip:
            target.service_status = status
            target.reason_code = code.lower()
    if cancelled:
        return current.model_copy(update={"coverage": coverage})
    return current.model_copy(
        update={
            "coverage": coverage,
            "errors": [
                *current.errors,
                {
                    "code": code,
                    "message": f"The device check for {ip} did not complete ({status})."
                    + (f" {detail}" if detail else ""),
                    "device_id": None,
                    "target_ip": ip,
                },
            ],
        }
    )
