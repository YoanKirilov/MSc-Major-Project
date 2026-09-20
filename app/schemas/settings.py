from __future__ import annotations

from pydantic import Field

from .common import StrictModel, iso_z, utc_now


class Settings(StrictModel):
    schema_version: int = 1
    revision: int = 1
    allowed_network: str | None = None
    interface: str | None = None
    profile_id: str = "tcp12-v1"
    retain_raw_xml: bool = False
    ai_enabled: bool = False
    ai_consent_revision: int = 0
    updated_at: str | None = Field(default_factory=lambda: iso_z(utc_now()))


class SettingsUpdate(StrictModel):
    expected_revision: int
    allowed_network: str | None = None
    interface: str | None = None
    retain_raw_xml: bool | None = None
    ai_enabled: bool | None = None
