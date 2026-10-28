"""Published vulnerability references, separate from assessed scan findings."""

from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from .advisory import CveAdvisory
from .common import StrictModel, iso_z, observation_time


class CveLookupRequest(StrictModel):
    # Correlation only, not authentication, a device identity or an NVD query.
    operation_id: UUID | None = None


class CveReference(StrictModel):
    cve_id: str = Field(pattern=r"^CVE-\d{4}-\d{4,19}$")
    description: str = Field(max_length=1200)
    advisories: list[CveAdvisory] = Field(default_factory=list, max_length=3)
    published_at: str | None = Field(default=None, max_length=80)
    modified_at: str | None = Field(default=None, max_length=80)

    @field_validator("published_at", "modified_at", mode="before")
    @classmethod
    def valid_optional_date(cls, value):
        # Old records have no dates; invalid external dates must not become facts.
        return iso_z(observation_time(value))


class CveOperationReceipt(StrictModel):
    operation_id: UUID
    # Legacy single-receipt records do not establish a completion timestamp.
    recorded_at: str | None = Field(default=None, max_length=80)


class CveLookup(StrictModel):
    service_id: str = Field(max_length=100)
    operation_id: str | None = Field(
        default=None,
        max_length=36,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )
    checked_at: str
    operation_receipts: list[CveOperationReceipt] = Field(default_factory=list, max_length=8)
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
    lookup_version: str | None = Field(default=None, max_length=80)
    related_query: str | None = Field(default=None, max_length=512)
    related_status: Literal[
        "not_requested", "candidates", "no_matches", "coverage_unknown", "unavailable"
    ] = "not_requested"
    related_total: int = Field(default=0, ge=0)
    related_results: list[CveReference] = Field(default_factory=list, max_length=5)
    related_truncated: bool = False
    related_unverified: int = Field(default=0, ge=0)
    related_examined: int = Field(default=0, ge=0, le=40)
    related_selection: Literal["legacy_first_page", "recent_first", "partial"] = "legacy_first_page"
    related_search_incomplete: bool = False
    ai_source: Literal["fixed", "ollama"] = "fixed"
    ai_model: str | None = Field(default=None, max_length=200)
    ai_prompt_version: str = "cve-context-1"
    ai_fallback_reason: str | None = Field(default=None, max_length=80)
    explanation: list[str] = Field(default_factory=list, max_length=6)
