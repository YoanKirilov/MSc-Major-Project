from __future__ import annotations

from pydantic import BaseModel

from .common import StrictModel


class ApiErrorEnvelope(StrictModel):
    error: dict[str, str | dict[str, str] | None] = {"code": "ERROR", "message": "An error occurred.", "details": None}


class ScanCreateRequest(StrictModel):
    mode: str
    cidr: str | None = None
    hosts: list[str] = []
    authorised: bool = False


class DemoScanRequest(StrictModel):
    scenario: str = "mixed-network-v1"


class DeviceCategoryUpdate(StrictModel):
    expected_revision: int
    user_category: str | None = None
