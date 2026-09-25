from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Callable
from uuid import UUID, uuid4

from app.schemas.common import iso_z, utc_now
from app.schemas.scan import ScanDocument
from app.schemas.settings import Settings, SettingsUpdate
from filelock import FileLock

logger = logging.getLogger(__name__)


class DocumentTooLarge(ValueError):
    pass


class JsonStore:
    max_document_bytes = 20 * 1024 * 1024

    def __init__(self, data_root: str | os.PathLike[str]):
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self._settings_lock = FileLock(str(self.data_root / "settings.lock"))

    def storage_writable(self) -> bool:
        """Exercise the same lock/write path used by scans, without touching user data."""
        probe = self.data_root / "locks" / f"probe-{uuid4().hex}.lock"
        temp = self.data_root / f".probe-{uuid4().hex}.tmp"
        try:
            probe.parent.mkdir(parents=True, exist_ok=True)
            with FileLock(str(probe), timeout=1):
                with temp.open("wb") as handle:
                    handle.write(b"ok")
                    handle.flush()
                    os.fsync(handle.fileno())
            return True
        except (OSError, TimeoutError):
            return False
        finally:
            for path in (temp, probe):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _scan_lock(self, scan_id: UUID | str) -> FileLock:
        canonical_id = str(UUID(str(scan_id)))
        lock_dir = self.data_root / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return FileLock(str(lock_dir / f"{canonical_id}.lock"))

    def _scan_dir(self, scan_id: UUID | str) -> Path:
        canonical_id = str(UUID(str(scan_id)))
        return self.data_root / "scans" / canonical_id

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.is_file() or path.is_symlink():
            raise ValueError("managed JSON file is not a regular file")
        if path.stat().st_size > self.max_document_bytes:
            raise ValueError("managed JSON file exceeds the size limit")

        def reject_duplicate_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON object key")
                result[key] = value
            return result

        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)

    def _atomic_write(self, path: Path, payload: str, backup: Path | None = None) -> None:
        # Check UTF-8 bytes before touching the existing file or its backup.
        if len(payload.encode("utf-8")) > self.max_document_bytes:
            raise DocumentTooLarge("managed JSON file exceeds the size limit")
        path.parent.mkdir(parents=True, exist_ok=True)
        if backup is not None and path.exists():
            self._atomic_write(backup, path.read_text(encoding="utf-8"))
        # A short, exclusively-created name avoids doubling long archive filenames.
        fd, temporary = tempfile.mkstemp(prefix=".w-", suffix=".tmp", dir=path.parent)
        temp_path = Path(temporary)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            self._retry_windows_file_operation(lambda: os.replace(temp_path, path))
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _retry_windows_file_operation(operation: Callable[[], Any]) -> None:
        """Tolerate short OneDrive/antivirus sharing locks without hiding real write failures."""
        for attempt in range(6):
            try:
                operation()
                return
            except PermissionError as exc:
                if getattr(exc, "winerror", None) not in {5, 32} or attempt == 5:
                    raise
                time.sleep(min(0.05 * 2**attempt, 0.4))

    def _write_scan(self, document: ScanDocument) -> ScanDocument:
        # model_copy(update=...) skips validation: validate BEFORE publishing JSON.
        document = ScanDocument.model_validate(document.model_dump(mode="json"))
        scan_dir = self._scan_dir(document.scan_id)
        path = scan_dir / "scan.json"

        def encode():
            return json.dumps(document.model_dump(mode="json"), ensure_ascii=False, allow_nan=False)

        payload = encode()
        archives = []
        while document.guidance_history and (
            len(document.guidance_history) > 3
            or len(payload.encode("utf-8")) > self.max_document_bytes
        ):
            snapshot = document.guidance_history.pop(0)
            name = f"guidance-{uuid4()}.json"
            archives.append(
                (name, json.dumps(snapshot.model_dump(mode="json"), ensure_ascii=False))
            )
            document.guidance_archives.append(name)
            payload = encode()
        # Validate the entire write set first. Never publish an unreadable report.
        if any(
            len(value.encode("utf-8")) > self.max_document_bytes
            for value in [payload, *(value for _, value in archives)]
        ):
            raise DocumentTooLarge(
                "scan evidence exceeds the JSON size limit; existing checkpoints are preserved"
            )
        for name, value in archives:
            self._atomic_write(scan_dir / "guidance" / name, value)
        self._atomic_write(
            path, payload, scan_dir / "scan.previous.json" if path.exists() else None
        )
        # A successful primary write includes the overlaid state and advances
        # revision. The old marker is now redundant; leave it inert if locked.
        try:
            (scan_dir / "terminal.json").unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove an absorbed terminal marker for %s", document.scan_id)
        summary = self._scan_summary(document)
        try:
            self._atomic_write(scan_dir / "summary.json", json.dumps(summary, ensure_ascii=False))
            self._atomic_write(scan_dir / "progress.json", json.dumps(self._progress(document)))
        except OSError:
            logger.warning("Could not refresh scan history summary for %s", document.scan_id)
        return ScanDocument.model_validate(json.loads(payload))

    @staticmethod
    def _scan_summary(document: ScanDocument) -> dict[str, Any]:
        severity_order = {"informational": 0, "low": 1, "medium": 2, "high": 3}
        highest = max(
            (finding.severity for finding in document.findings),
            key=severity_order.get,
            default=None,
        )
        return {
            "scan_id": document.scan_id,
            "state": document.state,
            "source": document.source,
            "created_at": document.created_at,
            "device_count": len(document.devices),
            "finding_count": len(document.findings),
            "highest_severity": highest,
            "storage_status": "ok",
            "revision": document.revision,
        }

    def _load_scan(self, scan_id: UUID | str) -> ScanDocument:
        path = self._scan_dir(scan_id) / "scan.json"
        if not path.exists():
            raise FileNotFoundError(scan_id)
        data = self._read_json(path)
        document = ScanDocument.model_validate(data)
        if document.scan_id != str(UUID(str(scan_id))):
            raise ValueError("Report ID does not match its storage folder")
        terminal = path.with_name("terminal.json")
        if terminal.is_file():
            marker = self._read_json(terminal)
            if (
                marker.get("base_revision") == document.revision
                and marker.get("scan_id") == document.scan_id
            ):
                allowed = {
                    "state",
                    "phase",
                    "finished_at",
                    "analysis_status",
                    "analysis_error",
                    "scan_outcome",
                    "coverage",
                    "errors",
                    "warnings",
                }
                changes = marker.get("updates", {})
                if not isinstance(changes, dict) or set(changes) - allowed:
                    raise ValueError("Invalid terminal status fields")
                document = ScanDocument.model_validate({**data, **changes})
        return document

    def _finish_scan(self, scan_id, mutate):
        """Keep terminal status writable even when evidence fills the document.

        The sidecar is revision-bound and never replaces observations. A later
        successful write absorbs its state and makes the old marker inert.
        """
        with self._scan_lock(scan_id):
            current = self._load_scan(scan_id)
            updated = mutate(current.model_copy(deep=True))
            if updated.phase != "finished" or updated.state in {"queued", "running"}:
                raise ValueError("Terminal update must finish the job")
            allowed = {
                "state",
                "phase",
                "finished_at",
                "analysis_status",
                "analysis_error",
                "scan_outcome",
                "coverage",
                "errors",
                "warnings",
            }
            before = current.model_dump(mode="json")
            after = updated.model_dump(mode="json")
            if any(
                before[key] != after[key]
                for key in ("devices", "services", "findings", "observations", "target")
            ):
                raise ValueError("Terminal update cannot change evidence")
            updated.revision = current.revision + 1
            try:
                return self._write_scan(updated)
            except DocumentTooLarge:
                # Compare to the primary, not an already overlaid terminal state.
                # Otherwise a second terminal update could erase the first one.
                primary = self._read_json(self._scan_dir(scan_id) / "scan.json")
                updates = {key: after[key] for key in allowed if primary.get(key) != after[key]}
                marker = {
                    "scan_id": current.scan_id,
                    "base_revision": current.revision,
                    "updates": updates,
                }
                self._atomic_write(self._scan_dir(scan_id) / "terminal.json", json.dumps(marker))
                return self._load_scan(scan_id)

    async def finish_scan(self, scan_id, mutate):
        return await asyncio.to_thread(self._finish_scan, scan_id, mutate)

    def _create_scan(self, document: ScanDocument) -> ScanDocument:
        with self._scan_lock(document.scan_id):
            return self._write_scan(document)

    async def create_scan(self, document: ScanDocument) -> ScanDocument:
        return await asyncio.to_thread(self._create_scan, document)

    async def load_scan(self, scan_id: UUID | str) -> ScanDocument:
        return await asyncio.to_thread(self._load_scan, scan_id)

    @staticmethod
    def _progress(document):
        coverage = document.coverage.model_dump(mode="json")
        coverage["targets"] = [
            {"service_status": item.service_status, "attempts": item.attempts}
            for item in document.coverage.targets
        ]
        return {
            "scan_id": document.scan_id,
            "source": document.source,
            "revision": document.revision,
            "state": document.state,
            "phase": document.phase,
            "analysis_status": document.analysis_status,
            "target": {"mode": document.target.get("mode")},
            "coverage": coverage,
            "device_count": len(document.devices),
            "finding_count": len(document.findings),
        }

    def _load_progress(self, scan_id):
        folder = self._scan_dir(scan_id)
        primary = folder / "scan.json"
        cache = folder / "progress.json"
        if not primary.is_file():
            raise FileNotFoundError(scan_id)
        if not (folder / "terminal.json").exists():
            try:
                if cache.stat().st_mtime_ns >= primary.stat().st_mtime_ns:
                    data = self._read_json(cache)
                    if data.get("scan_id") == str(scan_id) and data.get("state") in {
                        "queued",
                        "running",
                        "completed",
                        "partial",
                        "failed",
                        "cancelled",
                    }:
                        return data
            except (OSError, ValueError):
                pass
        return self._progress(self._load_scan(scan_id))

    async def load_progress(self, scan_id):
        return await asyncio.to_thread(self._load_progress, scan_id)

    async def load_guidance_archive(self, scan_id: str, name: str) -> dict:
        document = await self.load_scan(scan_id)
        if (
            not re.fullmatch(r"guidance-[0-9a-f-]{36}\.json", name)
            or name not in document.guidance_archives
        ):
            raise FileNotFoundError(name)
        return await asyncio.to_thread(self._read_json, self._scan_dir(scan_id) / "guidance" / name)

    def _update_scan(
        self,
        scan_id: UUID | str,
        mutate: Callable,
        expected_revision: int | None,
    ) -> ScanDocument:
        with self._scan_lock(scan_id):
            current = self._load_scan(scan_id)
            if expected_revision is not None and current.revision != expected_revision:
                raise ValueError("revision conflict")
            updated = mutate(current)
            updated.revision = current.revision + 1
            return self._write_scan(updated)

    async def update_scan(
        self, scan_id: UUID, mutate: Callable, expected_revision: int | None = None
    ) -> ScanDocument:
        return await asyncio.to_thread(self._update_scan, scan_id, mutate, expected_revision)

    def _list_scans(self, *, source: str | None, offset: int, limit: int) -> dict[str, Any]:
        scans_dir = self.data_root / "scans"
        if not scans_dir.exists():
            return {"items": [], "total": 0, "offset": offset, "limit": limit}
        items = []
        for scan_dir in scans_dir.iterdir():
            if not scan_dir.is_dir():
                continue
            scan_file = scan_dir / "scan.json"
            if not scan_file.exists():
                continue
            try:
                summary_file = scan_dir / "summary.json"
                item = None
                try:
                    if (
                        not (scan_dir / "terminal.json").exists()
                        and summary_file.is_file()
                        and not summary_file.is_symlink()
                        and summary_file.stat().st_mtime_ns >= scan_file.stat().st_mtime_ns
                    ):
                        cached = self._read_json(summary_file)
                        if (
                            cached.get("scan_id") == scan_dir.name
                            and cached.get("storage_status") == "ok"
                            and isinstance(cached.get("created_at"), str)
                        ):
                            item = cached
                except (OSError, ValueError, TypeError):
                    pass
                if item is None:
                    doc = self._load_scan(scan_dir.name)
                    item = self._scan_summary(doc)
                if source is not None and item["source"] != source:
                    continue
                item.pop("revision", None)
                items.append(item)
            except Exception:
                if source in {None, "live", "demo"}:
                    items.append(
                        {
                            "scan_id": scan_dir.name,
                            "state": None,
                            "source": None,
                            "created_at": None,
                            "device_count": None,
                            "finding_count": None,
                            "highest_severity": None,
                            "storage_status": "unreadable",
                        }
                    )
        items.sort(key=lambda item: item["created_at"] or "", reverse=True)
        return {
            "items": items[offset : offset + limit],
            "total": len(items),
            "offset": offset,
            "limit": limit,
        }

    async def list_scans(self, *, source: str | None, offset: int, limit: int) -> dict[str, Any]:
        return await asyncio.to_thread(
            self._list_scans,
            source=source,
            offset=offset,
            limit=limit,
        )

    def _list_incomplete_scan_ids(self) -> list[str]:
        scans_dir = self.data_root / "scans"
        if not scans_dir.exists():
            return []
        scan_ids = []
        for scan_dir in scans_dir.iterdir():
            scan_file = scan_dir / "scan.json"
            if not scan_dir.is_dir() or not scan_file.is_file():
                continue
            try:
                document = self._load_scan(scan_dir.name)
            except Exception:
                continue
            if document.source == "live" and (
                document.state in {"queued", "running"} or document.phase == "analysis"
            ):
                scan_ids.append(document.scan_id)
        return scan_ids

    async def list_incomplete_scan_ids(self) -> list[str]:
        return await asyncio.to_thread(self._list_incomplete_scan_ids)

    def _delete_scan(self, scan_id: UUID | str) -> None:
        with self._scan_lock(scan_id):
            scan_dir = self._scan_dir(scan_id)
            if scan_dir.exists():
                trash_dir = self.data_root / ".trash"
                trash_dir.mkdir(parents=True, exist_ok=True)
                destination = trash_dir / f"{scan_id}-{uuid4().hex}"
                os.rename(scan_dir, destination)

    async def delete_scan(self, scan_id: UUID | str) -> None:
        await asyncio.to_thread(self._delete_scan, scan_id)

    def _save_raw_output(self, scan_id: UUID | str, name: str, payload: bytes) -> None:
        if not re.fullmatch(r"(?:discovery|host-[0-9-]+)\.xml", name):
            raise ValueError("invalid raw output name")
        if len(payload) > self.max_document_bytes:
            raise ValueError("raw output exceeds the size limit")
        with self._scan_lock(scan_id):
            path = self._scan_dir(scan_id) / "raw" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=".w-", suffix=".tmp", dir=path.parent)
            temp_path = Path(temporary)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                self._retry_windows_file_operation(lambda: os.replace(temp_path, path))
            finally:
                if temp_path.exists():
                    temp_path.unlink()

    async def save_raw_output(self, scan_id: UUID | str, name: str, payload: bytes) -> None:
        await asyncio.to_thread(self._save_raw_output, scan_id, name, payload)

    def _load_settings(self) -> Settings:
        settings_file = self.data_root / "settings.json"
        if not settings_file.exists():
            return Settings()
        return Settings.model_validate(self._read_json(settings_file))

    async def load_settings(self) -> Settings:
        return await asyncio.to_thread(self._load_settings)

    def _update_settings(self, update: SettingsUpdate, expected_revision: int) -> Settings:
        with self._settings_lock:
            settings = self._load_settings()
            if settings.revision != expected_revision:
                raise ValueError("revision conflict")
            was_ai_enabled = settings.ai_enabled
            for field, value in update.model_dump(
                exclude={"expected_revision"}, exclude_unset=True
            ).items():
                setattr(settings, field, value)
            if not was_ai_enabled and settings.ai_enabled:
                settings.ai_consent_revision += 1
            settings.revision += 1
            settings.updated_at = iso_z(utc_now())
            path = self.data_root / "settings.json"
            payload = json.dumps(
                settings.model_dump(mode="json"), ensure_ascii=False, allow_nan=False
            )
            self._atomic_write(path, payload, self.data_root / "settings.previous.json")
            return settings

    async def update_settings(self, update: SettingsUpdate, expected_revision: int) -> Settings:
        return await asyncio.to_thread(self._update_settings, update, expected_revision)
