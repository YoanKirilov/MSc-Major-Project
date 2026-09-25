"""Validated, rebuildable views of a report for history and polling."""

from typing import Literal

from pydantic import NonNegativeInt, PositiveInt

from .common import StrictModel
from .scan import AnalysisStatus, FindingSeverity, HostCheckState, ScanPhase, ScanSource, ScanState


class ProgressTarget(StrictModel):
    service_status: HostCheckState
    attempts: NonNegativeInt


class ProgressCoverage(StrictModel):
    candidate_count: NonNegativeInt
    discovered_count: NonNegativeInt
    service_attempted_count: NonNegativeInt
    service_completed_count: NonNegativeInt
    service_failed_count: NonNegativeInt
    service_skipped_count: NonNegativeInt
    discovery_complete: bool
    service_stage_complete: bool
    targets: list[ProgressTarget]


class ProgressScope(StrictModel):
    mode: Literal["discover", "known_hosts", "demo"]


class ProgressSnapshot(StrictModel):
    scan_id: str
    source: ScanSource
    revision: PositiveInt
    state: ScanState
    phase: ScanPhase
    analysis_status: AnalysisStatus
    target: ProgressScope
    coverage: ProgressCoverage
    device_count: NonNegativeInt
    finding_count: NonNegativeInt


class HistorySummary(StrictModel):
    scan_id: str
    state: ScanState
    source: ScanSource
    created_at: str
    device_count: NonNegativeInt
    finding_count: NonNegativeInt
    highest_severity: FindingSeverity | None
    storage_status: Literal["ok"]
    revision: PositiveInt
