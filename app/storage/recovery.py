"""Reserve annotation recovery revisions under the caller's storage lock."""

from app.schemas.common import StrictModel
from pydantic import Field


class RecoveryRevision(StrictModel):
    revision: int = Field(ge=1)


def reserve_recovery_revision(store, primary, backup_revision):
    fence = primary.with_name(f"{primary.stem}.recovery.json")
    previous = (
        RecoveryRevision.model_validate(store._read_json(fence)).revision
        if fence.exists() or fence.is_symlink()
        else 0
    )
    revision = max(backup_revision + 2, previous + 1)
    # Reserve before publishing the primary, even if that later write fails.
    # Never reuse a revision held by an editor from an earlier recovery.
    store._atomic_write(fence, RecoveryRevision(revision=revision).model_dump_json())
    return revision
