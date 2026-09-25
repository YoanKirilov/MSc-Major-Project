from __future__ import annotations

from pydantic import Field

from .common import StrictModel


class ScanCreateRequest(StrictModel):
    mode: str
    cidr: str | None = None
    hosts: list[str] = Field(default_factory=list)
    authorised: bool = False
    profile: str = "light"


class RefreshGuidanceRequest(StrictModel):
    expected_revision: int = Field(ge=1)
