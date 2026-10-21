"""Bounded source outcomes, never device identity or a passed security check."""

from typing import Literal

from pydantic import Field

from .common import StrictModel


class NameDiagnostic(StrictModel):
    source: Literal["reverse_dns", "mdns"]
    status: Literal["found", "not_found", "timeout", "busy", "error", "not_checked"]
    elapsed_ms: int = Field(ge=0, le=60000)
