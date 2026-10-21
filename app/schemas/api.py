from __future__ import annotations

from typing import Annotated
from uuid import UUID

from app.scanner.commands import MAX_KNOWN_HOSTS
from pydantic import Field

from .common import StrictModel


class ScanCreateRequest(StrictModel):
    operation_id: UUID | None = None
    mode: str = Field(max_length=16)
    cidr: str | None = Field(default=None, max_length=18)
    hosts: list[Annotated[str, Field(min_length=1, max_length=15)]] = Field(
        default_factory=list, max_length=MAX_KNOWN_HOSTS
    )
    authorised: bool = False
    profile: str = Field(default="light", max_length=32)
    confirmed_scope: str | None = Field(default=None, max_length=43)


class RefreshGuidanceRequest(StrictModel):
    expected_revision: int = Field(ge=1)
    operation_id: UUID | None = None
