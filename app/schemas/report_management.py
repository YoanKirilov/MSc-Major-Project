"""Revision-bound, bounded requests for removing saved reports."""

from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .common import StrictModel


class ReportDeleteTarget(StrictModel):
    scan_id: str = Field(min_length=36, max_length=36)
    expected_revision: int = Field(ge=1, strict=True)
    expected_notes_revision: int = Field(ge=1, strict=True)

    @field_validator("scan_id")
    @classmethod
    def canonical_uuid(cls, value):
        if str(UUID(value)) != value:
            raise ValueError("Use a canonical report UUID")
        return value


class ReportDeleteRequest(StrictModel):
    reports: list[ReportDeleteTarget] = Field(min_length=1, max_length=24)

    @model_validator(mode="after")
    def unique_reports(self):
        if len({item.scan_id for item in self.reports}) != len(self.reports):
            raise ValueError("Select each report only once")
        return self


class ReportRestoreRequest(StrictModel):
    trash_ids: list[str] = Field(min_length=1, max_length=24)

    @field_validator("trash_ids")
    @classmethod
    def canonical_unique_uuids(cls, values):
        for value in values:
            if str(UUID(value)) != value:
                raise ValueError("Use canonical recovery UUIDs")
        if len(set(values)) != len(values):
            raise ValueError("Select each recovery copy only once")
        return values


class RemovalReceipt(ReportDeleteTarget):
    trash_id: str = Field(min_length=36, max_length=36)
    removed_at: str = Field(max_length=40)

    @field_validator("trash_id")
    @classmethod
    def canonical_trash_uuid(cls, value):
        if str(UUID(value)) != value:
            raise ValueError("Use a canonical recovery UUID")
        return value
