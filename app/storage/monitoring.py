"""Revisioned local periodic-check settings, without restoring execution authority."""

from __future__ import annotations

import asyncio
from typing import Literal
from uuid import UUID, uuid4

from app.schemas.common import StrictModel, iso_z, observation_time, utc_now
from app.security.scope import validate_target
from app.storage.report_trash import ReportTrash, UnsafeReportPath
from filelock import FileLock, Timeout
from pydantic import Field, StrictBool, StrictInt, field_validator, model_validator

MAX_EVENTS = 100
MAX_MONITOR_BYTES = 128 * 1024
Outcome = Literal["queued", "completed", "partial", "failed", "cancelled", "unavailable"]
PauseReason = Literal[
    "restarted",
    "network_changed",
    "network_unavailable",
    "storage_unavailable",
    "submission_failed",
]
EventKind = Literal[
    "enabled", "disabled", "paused", "deferred", "started", "result", "result_unavailable"
]


class MonitoringUnavailable(ValueError):
    pass


class MonitoringRevisionConflict(ValueError):
    pass


def canonical_id(value):
    if value is not None and str(UUID(value)) != value:
        raise ValueError("Use a canonical report identifier")
    return value


def recorded_time(value):
    if value is not None and observation_time(value) is None:
        raise ValueError("Use a recorded date with its timezone")
    return value


def valid_scope(value):
    if value is not None:
        validate_target(
            {"mode": "discover", "cidr": value, "authorised": True},
            {"allowed_network": value},
        )
    return value


class MonitoringCounts(StrictModel):
    device_count: StrictInt = Field(default=0, ge=0, le=100_000)
    finding_count: StrictInt = Field(default=0, ge=0, le=100_000)
    completed_count: StrictInt = Field(default=0, ge=0, le=100_000)
    unfinished_count: StrictInt = Field(default=0, ge=0, le=100_000)
    comparable_device_count: StrictInt = Field(default=0, ge=0, le=100_000)
    changed_device_count: StrictInt = Field(default=0, ge=0, le=100_000)


class MonitoringEvent(StrictModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()), min_length=36, max_length=36)
    occurred_at: str = Field(default_factory=lambda: iso_z(utc_now()), max_length=40)
    kind: EventKind
    message: str = Field(min_length=1, max_length=500)
    scan_id: str | None = Field(default=None, min_length=36, max_length=36)
    outcome: Outcome | None = None
    counts: MonitoringCounts | None = None

    _ids = field_validator("event_id", "scan_id")(canonical_id)
    _time = field_validator("occurred_at")(recorded_time)


class MonitoringDocument(StrictModel):
    schema_version: Literal[1] = 1
    revision: StrictInt = Field(default=1, ge=1)
    enabled: StrictBool = False
    scope: str | None = Field(default=None, max_length=18)
    interval_minutes: StrictInt = Field(default=60, ge=30, le=1440)
    next_check_at: str | None = Field(default=None, max_length=40)
    pause_reason: PauseReason | None = None
    last_scan_id: str | None = Field(default=None, min_length=36, max_length=36)
    last_outcome: Outcome | None = None
    events: list[MonitoringEvent] = Field(default_factory=list, max_length=MAX_EVENTS)

    _scope = field_validator("scope")(valid_scope)
    _ids = field_validator("last_scan_id")(canonical_id)
    _time = field_validator("next_check_at")(recorded_time)

    @model_validator(mode="after")
    def valid_enabled_schedule(self):
        if self.enabled and (self.scope is None or self.next_check_at is None or self.pause_reason):
            raise ValueError("An enabled schedule requires an approved scope and next check date")
        if not self.enabled and self.next_check_at is not None:
            raise ValueError("A paused schedule has no next check date")
        if len({event.event_id for event in self.events}) != len(self.events):
            raise ValueError("Duplicate monitoring events")
        return self


class MonitoringUpdate(StrictModel):
    expected_revision: StrictInt = Field(ge=1)
    enabled: StrictBool
    interval_minutes: StrictInt = Field(default=60, ge=30, le=1440)
    authorised: StrictBool = False
    confirmed_scope: str | None = Field(default=None, max_length=18)


def add_event(
    document, kind, message, *, occurred_at=None, scan_id=None, outcome=None, counts=None
):
    event = MonitoringEvent(
        kind=kind,
        message=message,
        occurred_at=occurred_at or iso_z(utc_now()),
        scan_id=scan_id,
        outcome=outcome,
        counts=counts,
    )
    keys = ("kind", "message", "scan_id", "outcome", "counts")
    if document.events and all(
        getattr(document.events[-1], key) == getattr(event, key) for key in keys
    ):
        return document
    return document.model_copy(update={"events": [*document.events, event][-MAX_EVENTS:]})


class MonitoringStore:
    def __init__(self, store):
        self.store = store
        self.path = store.data_root / "monitor.json"
        self.backup = store.data_root / "monitor.previous.json"
        self.lock_path = store.data_root / "monitor.lock"
        self.lock = FileLock(str(self.lock_path), timeout=5)
        self.safety = ReportTrash(store)

    def _safe_paths(self):
        root = self.store.data_root.resolve()
        for path in (self.path, self.backup, self.lock_path):
            try:
                self.safety._safe_path(path)
                if path.resolve().parent != root or (path.exists() and not path.is_file()):
                    raise UnsafeReportPath("Monitoring uses an unsafe local path")
            except (OSError, UnsafeReportPath) as exc:
                raise MonitoringUnavailable(
                    "Periodic check settings use an unsafe local path"
                ) from exc

    def _load(self):
        # Atomic replacement permits read-only startup/status; no default lock or JSON file.
        self._safe_paths()
        if not self.path.exists():
            if self.backup.exists():
                raise MonitoringUnavailable("Periodic check settings require backup recovery")
            return MonitoringDocument()
        try:
            if self.path.stat().st_size > MAX_MONITOR_BYTES:
                raise ValueError("Periodic check settings exceed the size limit")
            return MonitoringDocument.model_validate(self.store._read_json(self.path), strict=True)
        except (OSError, ValueError) as exc:
            raise MonitoringUnavailable("Periodic check settings could not be read safely") from exc

    async def load(self):
        return await asyncio.to_thread(self._load)

    def _replace(self, document, expected_revision):
        self._safe_paths()
        try:
            with self.lock:
                current = self._load()
                if current.revision != expected_revision:
                    raise MonitoringRevisionConflict(
                        "Periodic check settings changed; reload first"
                    )
                changed = MonitoringDocument.model_validate(
                    {**document.model_dump(), "revision": expected_revision + 1}, strict=True
                )
                payload = changed.model_dump_json(indent=2)
                if len(payload.encode("utf-8")) > MAX_MONITOR_BYTES:
                    raise MonitoringUnavailable("Periodic check settings exceed the size limit")
                self._safe_paths()
                self.store._atomic_write(
                    self.path, payload, self.backup if self.path.exists() else None
                )
                return changed
        except (OSError, Timeout) as exc:
            raise MonitoringUnavailable(
                "Periodic check settings could not be saved safely"
            ) from exc

    async def replace(self, document, expected_revision):
        return await asyncio.to_thread(self._replace, document, expected_revision)
