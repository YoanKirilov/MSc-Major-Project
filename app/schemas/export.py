from __future__ import annotations

from pydantic import Field

from .common import StrictModel


class ExportDocument(StrictModel):
    export_schema_version: int = 1
    exported_at: str
    source: str
    redacted: bool = True
    coverage: dict[str, int | bool] = Field(default_factory=dict)
    devices: list[dict[str, object]] = Field(default_factory=list)
    findings: list[dict[str, object]] = Field(default_factory=list)
