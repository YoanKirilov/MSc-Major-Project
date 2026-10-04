"""Editable presentation data; never overwrite original scan observations."""

import asyncio
from uuid import UUID

from app.schemas.common import StrictModel
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


class ReportAnnotations(StrictModel):
    revision: int = Field(default=1, ge=1)
    title: str = Field(default="", max_length=100)
    name_refreshes: list[NameRefresh] = Field(default_factory=list, max_length=256)
    cve_lookups: list[CveLookup] = Field(default_factory=list, max_length=128)


class AnnotationStore:
    def __init__(self, store):
        self.store = store

    def _load(self, scan_id):
        path = self.store._scan_dir(scan_id) / "annotations.json"
        return (
            ReportAnnotations.model_validate(self.store._read_json(path))
            if path.exists()
            else ReportAnnotations()
        )

    def _update(self, scan_id, *, title=None, refresh=None, cve=None):
        with self.store._scan_lock(scan_id):
            self.store._load_scan(scan_id)
            saved = self._load(scan_id)
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
