"""Editable presentation data; never overwrite original scan observations."""

import asyncio
import shutil
from typing import Literal
from uuid import UUID, uuid4

from app.schemas.common import StrictModel, iso_z, utc_now
from app.schemas.cve import CveLookup
from pydantic import Field, field_validator


class TitleUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    title: str = Field(max_length=100)

    @field_validator("title")
    @classmethod
    def single_line(cls, value):
        if any(not char.isprintable() for char in value):
            raise ValueError("Use a single-line report title")
        return value.strip()


class NameRefresh(StrictModel):
    device_id: UUID
    checked_at: str
    names: list[dict[str, str]] = Field(default_factory=list, max_length=16)
    notes: list[str] = Field(default_factory=list, max_length=8)


class ActionCheckUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    finding_id: str = Field(min_length=1, max_length=80)
    action_id: str = Field(min_length=1, max_length=120)
    status: Literal["to_check", "checked", "need_help"]


class ActionCheck(StrictModel):
    finding_id: str = Field(min_length=1, max_length=80)
    action_id: str = Field(min_length=1, max_length=120)
    status: Literal["checked", "need_help"]
    updated_at: str = Field(default_factory=lambda: iso_z(utc_now()))


class ReportAnnotations(StrictModel):
    revision: int = Field(default=1, ge=1)
    title: str = Field(default="", max_length=100)
    name_refreshes: list[NameRefresh] = Field(default_factory=list, max_length=256)
    cve_lookups: list[CveLookup] = Field(default_factory=list, max_length=128)
    action_checks: list[ActionCheck] = Field(default_factory=list, max_length=1024)
    recovery_notice: str | None = Field(default=None, max_length=300)


class AnnotationStore:
    def __init__(self, store):
        self.store = store

    def _load(self, scan_id):
        with self.store._scan_lock(scan_id):
            return self._load_locked(scan_id)

    def _load_locked(self, scan_id):
        path = self.store._scan_dir(scan_id) / "annotations.json"
        backup = path.with_name("annotations.previous.json")
        if (
            not path.exists()
            and not path.is_symlink()
            and not backup.exists()
            and not backup.is_symlink()
        ):
            return ReportAnnotations()
        try:
            return ReportAnnotations.model_validate(self.store._read_json(path))
        except (OSError, ValueError) as exc:
            saved = ReportAnnotations.model_validate(self.store._read_json(backup))
            # A normal primary is backup revision + 1. Skip it to invalidate stale tabs.
            recovered = saved.model_copy(
                update={
                    "revision": saved.revision + 2,
                    "recovery_notice": (
                        "Report notes were recovered from the previous backup. The latest edits "
                        "may be missing; original scan evidence is unchanged."
                    ),
                }
            )
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise ValueError("Refusing to replace an unsafe annotations path") from exc
            if path.exists():
                if path.stat().st_size > self.store.max_document_bytes:
                    raise ValueError("Oversized annotations require manual recovery") from exc
                shutil.copy2(path, path.with_name(f"annotations.corrupt-{uuid4().hex}.json"))
            # Never back up corrupt primary bytes over the validated previous version.
            self.store._atomic_write(path, recovered.model_dump_json(indent=2))
            return recovered

    def _update(self, scan_id, *, title=None, refresh=None, cve=None, action_check=None):
        with self.store._scan_lock(scan_id):
            document = self.store._load_scan(scan_id)
            saved = self._load_locked(scan_id)
            if action_check is not None:
                if document.source != "live" or document.phase != "finished":
                    raise ValueError(
                        "Wait for the live report to finish before editing its checklist"
                    )
                if saved.revision != action_check.expected_revision:
                    raise ValueError("Report notes changed; reload before saving your checklist")
                finding = next(
                    (f for f in document.findings if f.finding_id == action_check.finding_id), None
                )
                if finding is None or not any(
                    action.action_id == action_check.action_id for action in finding.actions
                ):
                    raise ValueError("This action is no longer in the saved report; reload first")
                saved.action_checks = [
                    check
                    for check in saved.action_checks
                    if (check.finding_id, check.action_id)
                    != (action_check.finding_id, action_check.action_id)
                ]
                if action_check.status != "to_check":
                    saved.action_checks.append(
                        ActionCheck(
                            finding_id=action_check.finding_id,
                            action_id=action_check.action_id,
                            status=action_check.status,
                        )
                    )
            if title is not None:
                if saved.revision != title.expected_revision:
                    raise ValueError("Report annotations changed; reload before saving")
                saved.title = title.title
            if refresh is not None:
                saved.name_refreshes = [
                    item for item in saved.name_refreshes if item.device_id != refresh.device_id
                ] + [refresh]
            if cve is not None:
                saved.cve_lookups = [
                    item for item in saved.cve_lookups if item.service_id != cve.service_id
                ] + [cve]
            changed = ReportAnnotations.model_validate(
                {**saved.model_dump(), "revision": saved.revision + 1}
            )
            path = self.store._scan_dir(scan_id) / "annotations.json"
            self.store._atomic_write(
                path, changed.model_dump_json(indent=2), path.with_name("annotations.previous.json")
            )
            return changed

    async def load(self, scan_id):
        return await asyncio.to_thread(self._load, scan_id)

    async def update(self, scan_id, **changes):
        return await asyncio.to_thread(self._update, scan_id, **changes)
