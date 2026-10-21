"""Read-only replay/AI audit of one explicit, isolated live-review artifact folder."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.explanations.report import report_input  # noqa: E402
from app.explanations.service import build_safe_findings  # noqa: E402
from app.explanations.validation import validated_line  # noqa: E402
from app.risk.engine import evaluate_device  # noqa: E402
from app.scanner.certificates import certificate_dates  # noqa: E402
from app.scanner.commands import DEEP_UDP_PORTS, PORTS, UDP_PORTS  # noqa: E402
from app.scanner.parser import parse_host  # noqa: E402
from app.storage.json_store import JsonStore  # noqa: E402


def projected_findings(findings):
    return sorted(
        (finding.model_dump(exclude={"created_at"}) for finding in findings),
        key=lambda value: value["finding_id"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", type=Path)
    args = parser.parse_args()
    run = args.artifacts.resolve(strict=True)
    if not run.is_relative_to(ROOT / ".test-artifacts"):
        parser.error("Use an explicit private artifact folder under .test-artifacts")
    store = JsonStore(run / "data")
    results = {}
    for profile in ("light", "deep"):
        scan_id = json.loads((run / f"{profile}-id.json").read_text())["scan_id"]
        document = store._load_scan(scan_id)
        if document.phase != "finished":
            parser.error("Wait for both scans to finish; this command never starts scans")
        services_replayed = 0
        certificates_revalidated = 0
        certificate_statuses = Counter()
        certificate_details_omitted = 0
        reproduced_findings = []
        targets = {target.ip: target for target in document.coverage.targets}
        missing = []
        for device in document.devices:
            target = targets.get(device.ip)
            if target is None or target.service_status != "completed":
                continue  # Unperformed checks must not be reported as successful replay.
            raw = store._scan_dir(scan_id) / "raw" / f"host-{device.ip.replace('.', '-')}.xml"
            if not raw.is_file():
                missing.append(device.device_id)
                continue
            parsed_device, services = parse_host(
                raw.read_bytes(),
                device.ip,
                scan_id,
                device.discovery_method,
                profile_tcp_ports=range(1, 65536) if profile == "deep" else PORTS,
                profile_udp_ports=DEEP_UDP_PORTS if profile == "deep" else UDP_PORTS,
                fill_unknown=profile != "deep",
            )
            saved = [
                service.model_dump(exclude={"observed_at"})
                for service in document.services
                if service.device_id == device.device_id
            ]
            if saved != [service.model_dump(exclude={"observed_at"}) for service in services]:
                raise ValueError("Replayed raw services differ from the saved evidence")
            services_replayed += len(services)
            if document.policy.get("extra_details_version") in {"1.0.2", "1.0.3"}:
                saved_times = {
                    service.service_id: service.observed_at for service in document.services
                }
                for service in services:
                    service.observed_at = saved_times[service.service_id]
                    interpretation = certificate_dates(service)
                    if interpretation is None:
                        continue
                    value, status = interpretation
                    entries = [
                        item
                        for item in device.details
                        if item.kind == "certificate"
                        and item.label == f"Connection certificate dates (port {service.port})"
                    ]
                    if not entries:
                        certificate_details_omitted += 1
                        continue  # Bounded optional enrichment can omit details, never a pass.
                    if len(entries) != 1 or (
                        entries[0].value,
                        entries[0].status,
                        entries[0].observed_at,
                    ) != (value, status, service.observed_at):
                        raise ValueError(
                            "Saved certificate interpretation differs from raw evidence"
                        )
                    certificates_revalidated += 1
                    certificate_statuses[status] += 1
            if [entry.model_dump() for entry in parsed_device.host_script_results] != [
                entry.model_dump() for entry in device.host_script_results
            ]:
                raise ValueError("Replayed host-script evidence differs from saved evidence")
            reproduced_findings.extend(
                evaluate_device(parsed_device, services, profile=document.policy.get("profile"))
            )
        saved_findings = [
            finding
            for finding in document.findings
            if targets.get(
                next(
                    device.ip
                    for device in document.devices
                    if device.device_id == finding.device_id
                )
            ).service_status
            == "completed"
        ]
        if projected_findings(saved_findings) != projected_findings(reproduced_findings):
            raise ValueError("Replayed deterministic findings differ from the saved findings")
        overview, overview_payload = report_input(document)
        inputs = [*build_safe_findings(document), overview_payload]
        serialized = json.dumps(inputs)
        identifiers = [document.target.get("cidr")]
        for device in document.devices:
            identifiers.extend([device.ip, device.mac, device.hostname])
        for target in document.coverage.targets:
            identifiers.extend([target.ip, target.discovery_mac, target.discovery_hostname])
        if any(identifier and identifier in serialized for identifier in identifiers):
            raise ValueError("Private network identifiers were found in the AI input")
        if "<nmaprun" in serialized:
            raise ValueError("Raw scanner XML was found in the AI input")
        findings = {finding.finding_id: finding for finding in [*document.findings, overview]}
        choices = {item["finding_id"]: item["reviewed_choices"] for item in inputs}
        records = [*document.explanations]
        if document.report_explanation:
            records.append(document.report_explanation)
        checked = 0
        for record in records:
            if record.status != "ready":
                continue
            finding = findings[record.finding_id]
            singles = {
                "title": (finding.title, record.display_title),
                "meaning": (finding.fixed_explanation.meaning, record.content.meaning),
                "why_it_matters": (
                    finding.fixed_explanation.why_it_matters,
                    record.content.why_it_matters,
                ),
            }
            for field, (original, output) in singles.items():
                if output is not None:
                    validated_line(
                        original,
                        output,
                        field=field,
                        rule_id=finding.rule_id,
                        reviewed_choices=choices[record.finding_id][field],
                    )
            for field, originals, outputs in (
                ("limitations", finding.limitations, record.display_limitations),
                (
                    "recommended_steps",
                    [action.text for action in finding.actions],
                    record.content.recommended_steps,
                ),
                (
                    "how_to_check",
                    [action.verification for action in finding.actions],
                    record.content.how_to_check,
                ),
            ):
                if outputs is not None:
                    if len(originals) != len(outputs):
                        raise ValueError("Generated guidance changed the number of factual lines")
                    for index, (original, output) in enumerate(
                        zip(originals, outputs, strict=True)
                    ):
                        validated_line(
                            original,
                            output,
                            field=field,
                            rule_id=finding.rule_id,
                            reviewed_choices=choices[record.finding_id][field][index],
                        )
            checked += 1
        results[profile] = {
            "scan_id": scan_id,
            "state": document.state,
            "coverage": document.coverage.model_dump(mode="json"),
            "device_count": len(document.devices),
            "open_services": sum(service.state == "open" for service in document.services),
            "findings": len(document.findings),
            "priorities": dict(Counter(finding.severity for finding in document.findings)),
            "services_replayed": services_replayed,
            "certificates_revalidated": certificates_revalidated,
            "certificate_statuses": dict(certificate_statuses),
            "certificate_details_omitted": certificate_details_omitted,
            "findings_replayed": len(reproduced_findings),
            "missing_raw_count": len(missing),
            "ai_status": document.analysis_status,
            "ai_records_revalidated": checked,
            "ai_record_statuses": dict(Counter(record.status for record in records)),
            "fallback_reasons": dict(
                Counter(record.fallback_reason for record in records if record.fallback_reason)
            ),
            "rejected_fields": sum(len(record.rejected_fields) for record in records),
            "identifier_free_ai_input": True,
            "errors": document.errors,
            "warnings": document.warnings,
            "named_devices": sum(bool(device.hostname) for device in document.devices),
            "name_sources": dict(
                Counter(device.hostname_source for device in document.devices if device.hostname)
            ),
            "name_lookup_outcomes": dict(
                Counter(
                    f"{item.source}:{item.status}"
                    for device in document.devices
                    for item in device.name_diagnostics
                )
            ),
            "max_name_lookup_elapsed_ms": max(
                (
                    item.elapsed_ms
                    for device in document.devices
                    for item in device.name_diagnostics
                ),
                default=None,
            ),
            "mdns_observations": len(document.observations),
            "selected_scripts": document.policy.get("selected_scripts", []),
            "configuration_checks_version": document.policy.get("configuration_checks_version"),
        }
    (run / "evidence-audit.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                profile: {
                    key: value
                    for key, value in result.items()
                    if key not in {"coverage", "errors", "warnings"}
                }
                for profile, result in results.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
