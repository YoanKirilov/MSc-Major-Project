from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def observation_time(value: object) -> datetime | None:
    """Read a saved instant without inventing a timezone or rewriting evidence."""
    if not isinstance(value, str):
        return None
    try:
        observed = datetime.fromisoformat(value)
        if observed.tzinfo is None:
            return None
        return observed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def iso_z(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        raise ValueError("naive datetime is not allowed")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
