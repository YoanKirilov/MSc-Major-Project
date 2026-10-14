"""Recoverable report removal, separate from scan cancellation and global names.

The caller must hold the supervisor admission lock and reject active job IDs.
The per-report file lock serialises this atomic directory move with evidence and
annotation writers. No files are permanently removed, and no report is restored
automatically. A private receipt keeps the original UUID and revisions beside
the archived evidence for revision-checked Undo or manual recovery.
"""

import asyncio
import logging
import os
import stat
import time
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.schemas.common import iso_z, utc_now
from app.schemas.report_management import RemovalReceipt
from app.storage.annotations import ReportAnnotations
from filelock import FileLock, Timeout

logger = logging.getLogger(__name__)


class UnsafeReportPath(ValueError):
    pass


class TrashFull(OSError):
    pass


class ReportTrash:
    # Fail closed without automatic purging. These are storage safety limits,
    # not a retention promise: operators retain control of recoverable evidence.
    max_reports = 1000
    max_bytes = 2 * 1024 * 1024 * 1024
    max_tree_entries = 100_000
    operation_timeout_s = 5

    def __init__(self, store):
        self.store = store
        self.root = store.data_root.resolve()

    def _safe_path(self, path: Path):
        # pathlib.is_junction was introduced after the supported Python 3.11.
        # On older Windows runtimes inspect the mount-point reparse tag instead.
        probe = getattr(path, "is_junction", None)
        if probe is not None:
            junction = probe()
        else:
            try:
                tag = getattr(path.lstat(), "st_reparse_tag", None)
                junction = tag is not None and tag == getattr(
                    stat, "IO_REPARSE_TAG_MOUNT_POINT", None
                )
            except FileNotFoundError:
                junction = False
        if path.is_symlink() or junction:
            raise UnsafeReportPath("Report paths must not redirect to another folder")
        if not path.resolve().is_relative_to(self.root):
            raise UnsafeReportPath("Report paths must stay in the managed data folder")

    def _tree_size(self, folder, deadline):
        """Inspect without following links, and bound work on damaged archives."""
        self._safe_path(folder)
        if not folder.is_dir():
            raise UnsafeReportPath("The managed archive must be a folder")
        pending = [folder]
        size = entries = 0
        while pending:
            if time.monotonic() >= deadline:
                raise TimeoutError("The recovery operation took too long")
            parent = pending.pop()
            for child in parent.iterdir():
                if time.monotonic() >= deadline:
                    raise TimeoutError("The recovery operation took too long")
                entries += 1
                if entries > self.max_tree_entries:
                    raise TrashFull("The recovery folder needs maintenance")
                self._safe_path(child)
                if child.is_dir():
                    pending.append(child)
                elif child.is_file():
                    size += child.stat().st_size
                else:
                    raise UnsafeReportPath("Report evidence must contain regular files")
                if size > self.max_bytes:
                    raise TrashFull("The recovery folder needs maintenance")
        return size

    def _notes_revision(self, folder):
        primary = folder / "annotations.json"
        self._safe_path(primary)
        if primary.exists():
            return ReportAnnotations.model_validate(self.store._read_json(primary)).revision
        # A missing primary with recovery material is not a pristine revision 1.
        # Do not recover or change optional notes as a side effect of removal.
        for name in ("annotations.previous.json", "annotations.recovery.json"):
            path = folder / name
            self._safe_path(path)
            if path.exists():
                raise ValueError("Saved report notes require recovery before removal")
        return 1

    def list_reports(self, *, offset=0, limit=24):
        """Read-only, bounded recovery index; unsafe entries are never followed."""
        from app.schemas.common import observation_time
        from app.storage.json_store import JsonStore

        deadline = time.monotonic() + self.operation_timeout_s
        trash = self.root / ".trash"
        for path in (self.store.data_root, trash, self.root / "report-trash.lock"):
            self._safe_path(path)
        if not trash.exists():
            return {"items": [], "total": 0, "offset": offset, "limit": limit, "warnings": []}
        receipts, warnings = [], set()
        with FileLock(str(self.root / "report-trash.lock"), timeout=self._lock_timeout(deadline)):
            for index, archive in enumerate(trash.iterdir()):
                self._check_deadline(deadline)
                if index >= self.max_reports:
                    raise TrashFull("The recovery folder needs maintenance")
                try:
                    self._safe_path(archive)
                    if str(UUID(archive.name)) != archive.name or not archive.is_dir():
                        raise ValueError("Invalid recovery folder")
                    path = archive / ".removal-receipt.json"
                    self._safe_path(path)
                    receipt = RemovalReceipt.model_validate(self.store._read_json(path))
                    if (
                        receipt.trash_id != archive.name
                        or observation_time(receipt.removed_at) is None
                    ):
                        raise ValueError("Invalid recovery receipt")
                    receipts.append((receipt, archive))
                except (OSError, ValueError):
                    warnings.add(
                        "Some recovery entries could not be read safely. Their files are preserved."
                    )
            receipts.sort(key=lambda entry: (entry[0].removed_at, entry[0].trash_id), reverse=True)
            items = []
            for receipt, archive in receipts[offset : offset + limit]:
                self._check_deadline(deadline)
                item = {
                    "trash_id": receipt.trash_id,
                    "scan_id": receipt.scan_id,
                    "removed_at": receipt.removed_at,
                    "restorable": False,
                }
                try:
                    size = self._tree_size(archive, deadline)
                    view = SimpleNamespace(
                        _read_json=self.store._read_json,
                        _scan_dir=lambda _id, folder=archive: folder,
                    )
                    saved = JsonStore._load_scan(view, receipt.scan_id)
                    notes_revision = self._notes_revision(archive)
                    notes = archive / "annotations.json"
                    title = (
                        ReportAnnotations.model_validate(self.store._read_json(notes)).title
                        if notes.exists()
                        else ""
                    )
                    item.update(
                        title=title,
                        profile=saved.policy.get("profile"),
                        target=saved.target,
                        created_at=saved.created_at,
                        bytes=size,
                        restorable=saved.revision == receipt.expected_revision
                        and notes_revision == receipt.expected_notes_revision
                        and saved.source == "live"
                        and saved.phase == "finished"
                        and saved.state not in {"queued", "running"}
                        and saved.analysis_status != "running",
                    )
                except (OSError, ValueError):
                    warnings.add(
                        "Some recovery copies need technical attention and cannot be restored. "
                        "Nothing was erased."
                    )
                items.append(item)
        return {
            "items": items,
            "total": len(receipts),
            "offset": offset,
            "limit": limit,
            "warnings": sorted(warnings),
        }

    @staticmethod
    def _check_deadline(deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("The recovery operation took too long")
        return remaining

    def _lock_timeout(self, deadline):
        return min(2, self.store.lock_timeout_s, self._check_deadline(deadline))

    @staticmethod
    def result(scan_id, status, message, **extra):
        return {"scan_id": scan_id, "status": status, "message": message, **extra}

    def _delete(self, target, *, deadline=None):
        scan_id = target.scan_id
        folder = self.store._scan_dir(scan_id)
        trash = self.root / ".trash"
        deadline = min(deadline or float("inf"), time.monotonic() + self.operation_timeout_s)
        try:
            # Check parent directories BEFORE acquiring locks or traversing.
            for path in (
                self.store.data_root,
                self.root / "scans",
                self.root / "locks",
                self.root / "locks" / f"{scan_id}.lock",
                self.root / "report-trash.lock",
                folder,
                trash,
            ):
                self._safe_path(path)
            if not folder.exists():
                return self.result(scan_id, "missing", "This report was already removed.")
            with FileLock(
                str(self.root / "report-trash.lock"), timeout=self._lock_timeout(deadline)
            ):
                with self.store._scan_lock(scan_id).acquire(timeout=self._lock_timeout(deadline)):
                    self._safe_path(folder)
                    if not folder.exists():
                        return self.result(scan_id, "missing", "This report was already removed.")
                    # The same per-report lock covers reads, revisions, and move.
                    # Source files are validated before any archive is created.
                    size = self._tree_size(folder, deadline)
                    document = self.store._load_scan(scan_id)
                    if document.source != "live":
                        return self.result(
                            scan_id, "unavailable", "Only saved live reports can be removed."
                        )
                    if (
                        document.phase != "finished"
                        or document.state in {"queued", "running"}
                        or document.analysis_status == "running"
                    ):
                        return self.result(
                            scan_id, "active", "Wait for this report to finish before removing it."
                        )
                    notes_revision = self._notes_revision(folder)
                    if (
                        document.revision != target.expected_revision
                        or notes_revision != target.expected_notes_revision
                    ):
                        return self.result(
                            scan_id,
                            "changed",
                            "This report changed. Reload and review it before removing it.",
                        )
                    trash.mkdir(exist_ok=True)
                    self._safe_path(trash)
                    for index, _entry in enumerate(trash.iterdir()):
                        self._check_deadline(deadline)
                        if index >= self.max_reports - 1:
                            raise TrashFull("The recovery folder needs maintenance")
                    trash_id = str(uuid4())
                    destination = trash / trash_id
                    self._safe_path(destination)
                    if destination.exists():
                        raise ValueError("A recovery folder with this receipt already exists")
                    receipt = RemovalReceipt(
                        **target.model_dump(), trash_id=trash_id, removed_at=iso_z(utc_now())
                    )
                    receipt_payload = receipt.model_dump_json()
                    if (
                        self._tree_size(trash, deadline)
                        + size
                        + len(receipt_payload.encode("utf-8"))
                        > self.max_bytes
                    ):
                        raise TrashFull("The recovery folder needs maintenance")
                    # Metadata is prepared before the move. It never replaces
                    # factual scan/notes files, even if a subsequent rename fails.
                    receipt_path = folder / ".removal-receipt.json"
                    self._safe_path(receipt_path)
                    self._check_deadline(deadline)
                    self.store._atomic_write(receipt_path, receipt_payload)
                    # One same-volume directory rename publishes removal atomically:
                    # crash before -> report remains; crash after -> whole report is
                    # recoverable with its original UUID receipt. Never copy then erase.
                    self._check_deadline(deadline)
                    self.store._retry_windows_file_operation(lambda: os.rename(folder, destination))
                    # The move is authoritative. Cache cleanup is best effort and
                    # may never turn successful removal into "files unchanged".
                    try:
                        with self.store.library_cache.lock:
                            cached = self.store.library_cache.entries.pop(scan_id, None)
                            if cached:
                                self.store.library_cache.size -= cached[2]
                    except Exception:
                        logger.warning(
                            "Removed report projection could not be evicted: %s", scan_id
                        )
                    return self.result(
                        scan_id,
                        "deleted",
                        "Removed from saved reports; a local recovery copy is retained.",
                        trash_id=trash_id,
                    )
        except TrashFull:
            return self.result(
                scan_id,
                "unavailable",
                "The local recovery folder is full or needs maintenance. "
                "This report has not been removed.",
            )
        except UnsafeReportPath:
            return self.result(
                scan_id,
                "unavailable",
                "This report's storage path could not be verified. "
                "Its files have not been changed.",
            )
        except FileNotFoundError:
            # A present folder with missing evidence is damage, not confirmed removal.
            return self.result(
                scan_id,
                "unavailable",
                "This report could not be read safely. Its files have not been changed.",
            )
        except (OSError, ValueError, Timeout):
            return self.result(
                scan_id,
                "unavailable",
                "This report could not be removed safely. "
                "Its evidence and notes have not been changed; try reloading it.",
            )

    @staticmethod
    async def _complete_thread(operation):
        """Cancellation must not release admission while a thread can still move."""
        task = asyncio.create_task(asyncio.to_thread(operation))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
            # Retrieve any worker exception before propagating cancellation.
            try:
                task.result()
            finally:
                raise asyncio.CancelledError from None

    async def delete(self, target, *, deadline=None):
        return await self._complete_thread(lambda: self._delete(target, deadline=deadline))

    def _restore(self, trash_id, *, deadline=None):
        # Validate internal callers too: no path can be built from arbitrary text.
        if str(UUID(trash_id)) != trash_id:
            raise ValueError("Use a canonical recovery UUID")
        archive = self.root / ".trash" / trash_id
        result = {"trash_id": trash_id}
        deadline = min(deadline or float("inf"), time.monotonic() + self.operation_timeout_s)
        try:
            for path in (
                self.store.data_root,
                self.root / "scans",
                self.root / "locks",
                self.root / "report-trash.lock",
                self.root / ".trash",
                archive,
            ):
                self._safe_path(path)
            with FileLock(
                str(self.root / "report-trash.lock"), timeout=self._lock_timeout(deadline)
            ):
                if not archive.exists():
                    return {
                        **result,
                        "status": "missing",
                        "message": "This recovery copy is no longer available.",
                    }
                self._tree_size(archive, deadline)
                receipt = RemovalReceipt.model_validate(
                    self.store._read_json(archive / ".removal-receipt.json")
                )
                if receipt.trash_id != trash_id:
                    raise ValueError("The recovery receipt does not match this folder")
                result["scan_id"] = receipt.scan_id
                destination = self.store._scan_dir(receipt.scan_id)
                self._safe_path(destination)
                self._safe_path(self.root / "locks" / f"{receipt.scan_id}.lock")
                with self.store._scan_lock(receipt.scan_id).acquire(
                    timeout=self._lock_timeout(deadline)
                ):
                    if destination.exists():
                        return {
                            **result,
                            "status": "changed",
                            "message": "A report with this ID already exists. "
                            "Neither copy has been replaced.",
                        }
                    # The report may use the terminal sidecar. Validate through a
                    # read-only view with the same loader, not just primary state.
                    from app.storage.json_store import JsonStore

                    view = SimpleNamespace(
                        _read_json=self.store._read_json, _scan_dir=lambda _scan_id: archive
                    )
                    saved = JsonStore._load_scan(view, receipt.scan_id)
                    if (
                        saved.revision != receipt.expected_revision
                        or self._notes_revision(archive) != receipt.expected_notes_revision
                        or saved.source != "live"
                        or saved.phase != "finished"
                        or saved.state in {"queued", "running"}
                        or saved.analysis_status == "running"
                    ):
                        return {
                            **result,
                            "status": "changed",
                            "message": "This recovery copy changed and cannot be "
                            "restored automatically.",
                        }
                    destination.parent.mkdir(exist_ok=True)
                    self._check_deadline(deadline)
                    self.store._retry_windows_file_operation(
                        lambda: os.rename(archive, destination)
                    )
                    return {
                        **result,
                        "status": "restored",
                        "message": "The saved report and its notes have been restored.",
                    }
        except (OSError, ValueError, Timeout):
            return {
                **result,
                "status": "unavailable",
                "message": "This report could not be restored safely. Existing reports "
                "and the recovery copy have not been replaced.",
            }

    async def restore(self, trash_id, *, deadline=None):
        return await self._complete_thread(lambda: self._restore(trash_id, deadline=deadline))
