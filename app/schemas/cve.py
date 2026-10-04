"""Published vulnerability references, separate from assessed scan findings."""

from typing import Literal

from pydantic import Field

from .common import StrictModel


class CveReference(StrictModel):
    cve_id: str = Field(pattern=r"^CVE-\d{4}-\d{4,19}$")
    description: str = Field(max_length=1200)


class CveLookup(StrictModel):
    service_id: str = Field(max_length=100)
    checked_at: str
    query: str | None = Field(default=None, max_length=512)
    resolved_query: str | None = Field(default=None, max_length=512)
    resolution: str | None = Field(default=None, max_length=80)
    identity_evidence: list[str] = Field(default_factory=list, max_length=40)
    status: Literal[
        "candidates", "no_matches", "identity_unresolved", "insufficient_evidence", "unavailable"
    ]
    total: int = Field(default=0, ge=0)
    results: list[CveReference] = Field(default_factory=list, max_length=5)
    truncated: bool = False
    message: str = Field(max_length=600)
    ai_source: Literal["fixed", "ollama"] = "fixed"
    ai_model: str | None = Field(default=None, max_length=200)
    ai_prompt_version: str = "cve-context-1"
    ai_fallback_reason: str | None = Field(default=None, max_length=80)
    explanation: list[str] = Field(default_factory=list, max_length=6)
