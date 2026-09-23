from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import re
import time
from pathlib import Path
from typing import Any, Callable
from uuid import UUID, uuid4

from filelock import FileLock

from app.schemas.scan import ScanDocument
from app.schemas.common import iso_z, utc_now
from app.schemas.settings import Settings, SettingsUpdate

logger = logging.getLogger(__name__)

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
        path.parent.mkdir(parents=True, exist_ok=True)
        if backup is not None and path.exists():
            self._retry_windows_file_operation(lambda: shutil.copyfile(path, backup))
        temp_path = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
        try:
            with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
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
                time.sleep(min(0.05 * 2 ** attempt, 0.4))

    def _write_scan(self, document: ScanDocument) -> ScanDocument:
        scan_dir = self._scan_dir(document.scan_id)
        path = scan_dir / "scan.json"
        payload = json.dumps(document.model_dump(mode="json"), ensure_ascii=False, allow_nan=False)
        self._atomic_write(path, payload, scan_dir / "scan.previous.json" if path.exists() else None)
        summary = self._scan_summary(document)
        try:
            self._atomic_write(scan_dir / "summary.json", json.dumps(summary, ensure_ascii=False))
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
        return ScanDocument.model_validate(data)

    def _create_scan(self, document: ScanDocument) -> ScanDocument:
        with self._scan_lock(document.scan_id):
            return self._write_scan(document)

    async def create_scan(self, document: ScanDocument) -> ScanDocument:
        return await asyncio.to_thread(self._create_scan, document)

    async def load_scan(self, scan_id: UUID | str) -> ScanDocument:
        return await asyncio.to_thread(self._load_scan, scan_id)

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

    async def update_scan(self, scan_id: UUID, mutate: Callable, expected_revision: int | None = None) -> ScanDocument:
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
                    if (summary_file.is_file() and not summary_file.is_symlink()
                            and summary_file.stat().st_mtime_ns >= scan_file.stat().st_mtime_ns):
                        cached = self._read_json(summary_file)
                        if (cached.get("scan_id") == scan_dir.name
                                and cached.get("storage_status") == "ok"
                                and isinstance(cached.get("created_at"), str)):
                            item = cached
                except (OSError, ValueError, TypeError):
                    pass
                if item is None:
                    doc = ScanDocument.model_validate(self._read_json(scan_file))
                    item = self._scan_summary(doc)
                if source is not None and item["source"] != source:
                    continue
                item.pop("revision", None)
                items.append(item)
            except Exception:
                if source in {None, "live", "demo"}:
                    items.append({
                        "scan_id": scan_dir.name,
                        "state": None,
                        "source": None,
                        "created_at": None,
                        "device_count": None,
                        "finding_count": None,
                        "highest_severity": None,
                        "storage_status": "unreadable",
                    })
        items.sort(key=lambda item: item["created_at"] or "", reverse=True)
        return {"items": items[offset: offset + limit], "total": len(items), "offset": offset, "limit": limit}

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
                document = ScanDocument.model_validate(self._read_json(scan_file))
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
            temp_path = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
            try:
                with temp_path.open("wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_path, path)
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
