from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .common import StrictModel, iso_z, utc_now

ServiceState = Literal[
    "open", "closed", "filtered", "open_filtered", "closed_filtered", "unfiltered", "unknown"
]
FindingSeverity = Literal["high", "medium", "low", "informational"]
FindingConfidence = Literal["high", "medium", "low"]
ScanSource = Literal["live", "demo"]


class DeviceProfile(StrictModel):
    category: Literal["camera", "printer", "router", "iot_other", "computer", "unknown"] = "unknown"
    confidence: Literal["low", "medium"] = "low"
    hints: list[dict[str, str]] = Field(default_factory=list)
    conflict: bool = False


class ScriptEvidence(StrictModel):
    script_id: str
    output: str
    truncated: bool = False


class Device(StrictModel):
    device_id: str
    scan_id: str
    ip: str
    hostname: str | None = None
    hostname_source: str | None = None
    hostname_observed_at: str | None = None
    hostname_confidence: Literal["low", "medium"] = "low"
    hostname_conflict: bool = False
    name_candidates: list[dict[str, str]] = Field(default_factory=list)
    mac: str | None = None
    vendor: str | None = None
    discovery_method: Literal["nmap_discovery", "mdns_advertisement", "known_host", "demo"] = (
        "known_host"
    )
    reachability: Literal["observed", "advertised", "unconfirmed"] = "unconfirmed"
    reachability_evidence: list[str] = Field(default_factory=list)
    host_script_results: list[ScriptEvidence] = Field(default_factory=list)
    profile: DeviceProfile = Field(default_factory=DeviceProfile)
    user_category: str | None = None
    observed_at: str = Field(default_factory=lambda: iso_z(utc_now()))


class Service(StrictModel):
    service_id: str
    device_id: str
    protocol: Literal["tcp", "udp"] = "tcp"
    port: int
    state: ServiceState = "unknown"
    state_reason: str | None = None
    name: str | None = None
    product: str | None = None
    version: str | None = None
    extra_info: str | None = None
    detection_method: Literal["probed", "table", "unknown"] = "unknown"
    nmap_confidence: int | None = None
    tunnel: str | None = None
    script_results: list[ScriptEvidence] = Field(default_factory=list)
    observed_at: str = Field(default_factory=lambda: iso_z(utc_now()))

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        if value < 1 or value > 65535:
            raise ValueError("unsupported port")
        return value


class EvidenceItem(StrictModel):
    field: str
    value: str | int | bool | None


class ActionRecord(StrictModel):
    action_id: str
    text: str
    verification: str


class FixedExplanation(StrictModel):
    meaning: str
    why_it_matters: str
    recommended_steps: list[str]
    how_to_check: list[str]


class Finding(StrictModel):
    finding_id: str
    device_id: str
    service_id: str
    rule_id: str
    rule_version: str
    title: str
    severity: FindingSeverity = "informational"
    confidence: FindingConfidence = "low"
    evidence: list[EvidenceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    fixed_explanation: FixedExplanation
    actions: list[ActionRecord] = Field(default_factory=list)
    references: list[dict[str, str]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: iso_z(utc_now()))


class ExplanationRecord(StrictModel):
    finding_id: str
    status: Literal["pending", "ready", "fallback"] = "fallback"
    source: Literal["ai", "fixed"] = "fixed"
    input_hash: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    rule_version: str | None = None
    requested_at: str | None = None
    completed_at: str | None = None
    consent_revision: int | None = None
    fallback_reason: str | None = None
    content: FixedExplanation | None = None
    display_title: str | None = None
    display_limitations: list[str] | None = None
    rejected_fields: dict[str, str] = Field(default_factory=dict)
    ai_fields: list[
        Literal[
            "title", "meaning", "why_it_matters", "limitations", "recommended_steps", "how_to_check"
        ]
    ] = Field(default_factory=list)


class TargetLedgerEntry(StrictModel):
    ip: str
    discovery_status: Literal["not_run", "observed", "not_seen", "unknown"] = "not_run"
    service_status: Literal[
        "not_scheduled",
        "pending",
        "running",
        "completed",
        "failed",
        "timed_out",
        "cancelled",
        "skipped",
    ] = "not_scheduled"
    reason_code: str | None = None
    attempts: int = 0
    discovery_sources: list[Literal["nmap", "mdns"]] = Field(default_factory=list)
    discovery_mac: str | None = None
    discovery_hostname: str | None = None
    discovery_vendor: str | None = None


class DiscoveryObservation(StrictModel):
    source: Literal["mdns"] = "mdns"
    evidence_type: Literal["advertisement"] = "advertisement"
    ip: str
    advertised_name: str
    service_type: str
    observed_at: str = Field(default_factory=lambda: iso_z(utc_now()))


class Coverage(StrictModel):
    candidate_count: int = 0
    discovered_count: int = 0
    service_attempted_count: int = 0
    service_completed_count: int = 0
    service_failed_count: int = 0
    service_skipped_count: int = 0
    discovery_complete: bool = False
    service_stage_complete: bool = False
    targets: list[TargetLedgerEntry] = Field(default_factory=list)


class GuidanceSnapshot(StrictModel):
    saved_at: str
    versions: dict[str, str | None]
    findings: list[Finding]
    explanations: list[ExplanationRecord]


class ScanDocument(StrictModel):
    schema_version: Literal[1] = 1
    revision: int = 1
    scan_id: str
    source: ScanSource = "live"
    created_at: str = Field(default_factory=lambda: iso_z(utc_now()))
    started_at: str | None = None
    finished_at: str | None = None
    state: Literal["queued", "running", "completed", "partial", "failed", "cancelled"] = "queued"
    phase: Literal["queued", "discovery", "service_scan", "analysis", "finished"] = "queued"
    target: dict[str, object] = Field(
        default_factory=lambda: {"mode": "discover", "cidr": None, "hosts": []}
    )
    policy: dict[str, object] = Field(default_factory=dict)
    versions: dict[str, str | None] = Field(
        default_factory=lambda: {
            "app": "0.1.0",
            "rules": "1.2.0",
            "profiling": "1.0.0",
            "prompt": "3.0.0",
            "nmap": None,
        }
    )
    coverage: Coverage = Field(default_factory=Coverage)
    observations: list[DiscoveryObservation] = Field(default_factory=list)
    devices: list[Device] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    explanations: list[ExplanationRecord] = Field(default_factory=list)
    guidance_history: list[GuidanceSnapshot] = Field(default_factory=list)
    guidance_archives: list[str] = Field(default_factory=list)
    report_explanation: ExplanationRecord | None = None
    scan_outcome: Literal["completed", "partial", "failed", "cancelled"] | None = None
    analysis_status: Literal["not_started", "running", "ready", "failed"] = "not_started"
    analysis_error: str | None = None
    guidance_updated_at: str | None = None
    ai_requests_used: int = 0
    warnings: list[dict[str, str]] = Field(default_factory=list)
    errors: list[dict[str, str | None]] = Field(default_factory=list)

    @field_validator("scan_id")
    @classmethod
    def validate_scan_id(cls, value: str):
        if not value or not isinstance(value, str):
            raise ValueError("scan_id must be a non-empty UUID string")
        try:
            UUID(value)
        except ValueError as exc:
            raise ValueError("scan_id must be a valid UUID string") from exc
        return str(value)

    @model_validator(mode="after")
    def validate_target_shape(self):
        target = self.target or {}
        mode = target.get("mode")
        hosts = target.get("hosts", [])
        cidr = target.get("cidr")
        if mode not in {"discover", "known_hosts", "demo"}:
            raise ValueError("target.mode must be discover, known_hosts, or demo")
        if mode == "discover":
            if cidr is None:
                raise ValueError("discover mode requires a cidr")
            if hosts:
                raise ValueError("discover mode must not include hosts")
        elif mode == "known_hosts":
            if cidr is not None:
                raise ValueError("known_hosts mode must not include a cidr")
            if not isinstance(hosts, list) or not hosts:
                raise ValueError("known_hosts mode requires at least one host")
        else:
            if cidr is not None or hosts:
                raise ValueError("demo mode must not include cidr or hosts")
        return self
