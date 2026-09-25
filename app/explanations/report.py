"""Source-bound wording for the whole report, including scans with no findings."""

from app.schemas.scan import Finding, FixedExplanation, ScanDocument


def report_input(document: ScanDocument) -> tuple[Finding, dict]:
    coverage = document.coverage
    count = len(document.devices)
    open_count = sum(service.state == "open" for service in document.services)
    finding_count = len(document.findings)
    devices = f"{count} device{'s' if count != 1 else ''}"
    connections = f"{open_count} service{'s' if open_count != 1 else ''}"
    meaning = (
        f"Recorded results for {devices} and {open_count} open "
        f"service{'s' if open_count != 1 else ''} in the selected checks."
    )
    meaning_plain = (
        f"The scan saved results for {devices}. It found {connections} accepting requests. "
        "A service is a device feature that other devices can contact, such as file sharing."
    )
    why = (
        f"The selected rules produced {finding_count} "
        f"finding{'s' if finding_count != 1 else ''} for review."
    )
    why_plain = (
        f"There {'is' if finding_count == 1 else 'are'} {finding_count} "
        f"item{'s' if finding_count != 1 else ''} to review. "
        "These are observations to check, not proof of a break-in."
    )
    high_count = sum(item.severity == "high" for item in document.findings)
    if high_count:
        why_plain += (
            f" {high_count} {'is' if high_count == 1 else 'are'} marked high priority: "
            f"review {'this' if high_count == 1 else 'these'} first."
        )
    if not coverage.service_completed_count:
        limitation = "No device checks completed. Device security could not be assessed."
        limitation_plain = (
            "The scan could not finish checking any devices, so it cannot tell "
            "you about their security."
        )
    elif coverage.service_failed_count or document.scan_outcome in {
        "partial",
        "failed",
        "cancelled",
    }:
        limitation = (
            "Some selected checks did not finish. The report covers only the "
            "observations that were saved."
        )
        limitation_plain = (
            "Some checks could not finish. These results describe only what "
            "the completed checks found."
        )
    else:
        limitation = (
            "Only the selected checks were run. Devices that did not respond "
            "and other security settings may remain unassessed."
        )
        limitation_plain = (
            "This scan checked a limited set of things. It may miss silent "
            "devices and security problems outside those checks."
        )
    step = "Review the findings and their recommended steps before making changes."
    step_plain = (
        "Start with the first item in the report and follow its suggested "
        "checks before changing settings."
    )
    if not finding_count:
        step = (
            "Review scan coverage. No findings does not establish that a "
            "device or network is secure."
        )
        step_plain = (
            "Look at what the scan managed to check. An empty findings list "
            "does not mean everything is safe."
        )
    if coverage.service_failed_count:
        step = (
            "Review the saved findings and retry unfinished device checks "
            "before drawing conclusions about the full scan."
        )
        step_plain = (
            "Review any listed items. Then choose Retry unfinished device "
            "checks. Devices that could not be checked still need attention."
        )
    check = (
        f"Device checks completed: {coverage.service_completed_count}; "
        f"device checks unsuccessful: {coverage.service_failed_count}."
    )
    check_plain = (
        f"Checks finished for {coverage.service_completed_count} "
        f"device{'s' if coverage.service_completed_count != 1 else ''}; "
        f"checks could not finish for {coverage.service_failed_count} "
        f"device{'s' if coverage.service_failed_count != 1 else ''}."
    )
    finding = Finding(
        finding_id="report-overview",
        device_id="report",
        service_id="report",
        rule_id="REPORT",
        rule_version="1.0.0",
        title="Your scan results explained",
        limitations=[limitation],
        fixed_explanation=FixedExplanation(
            meaning=meaning,
            why_it_matters=why,
            recommended_steps=[step],
            how_to_check=[check],
        ),
        actions=[{"action_id": "review", "text": step, "verification": check}],
    )
    choices = {
        "title": [finding.title],
        "meaning": [meaning, meaning_plain],
        "why_it_matters": [why, why_plain],
        "limitations": [[limitation, limitation_plain]],
        "recommended_steps": [[step, step_plain]],
        "how_to_check": [[check, check_plain]],
    }
    return finding, {
        "finding_id": finding.finding_id,
        "reviewed_choices": choices,
        "verified_title": finding.title,
        "verified_meaning": meaning,
        "verified_why_it_matters": why,
        "verified_limitations": [limitation],
        "verified_recommended_steps": [step],
        "verified_how_to_check": [check],
    }
