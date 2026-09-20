from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from filelock import FileLock

from app.schemas.export import ExportDocument
from app.schemas.scan import ScanDocument
from app.schemas.settings import Settings, SettingsUpdate


class JsonStore:
    max_document_bytes = 20 * 1024 * 1024

    def __init__(self, data_root: str | os.PathLike[str]):
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self._settings_lock = FileLock(str(self.data_root / "settings.lock"))

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
            shutil.copyfile(path, backup)
        temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    async def create_scan(self, document: ScanDocument) -> ScanDocument:
        scan_dir = self._scan_dir(document.scan_id)
        path = scan_dir / "scan.json"
        payload = json.dumps(document.model_dump(mode="json"), ensure_ascii=False, allow_nan=False)
        self._atomic_write(path, payload, scan_dir / "scan.previous.json" if path.exists() else None)
        return ScanDocument.model_validate(json.loads(payload))

    async def load_scan(self, scan_id: UUID) -> ScanDocument:
        path = self._scan_dir(scan_id) / "scan.json"
        if not path.exists():
            raise FileNotFoundError(scan_id)
        data = self._read_json(path)
        return ScanDocument.model_validate(data)

    async def update_scan(self, scan_id: UUID, mutate: Callable, expected_revision: int | None = None) -> ScanDocument:
        current = await self.load_scan(scan_id)
        if expected_revision is not None and current.revision != expected_revision:
            raise ValueError("revision conflict")
        updated = mutate(current)
        updated.revision = current.revision + 1
        return await self.create_scan(updated)

    async def mutate_with_settings(self, scan_id: UUID, mutate: Callable) -> ScanDocument:
        with self._settings_lock:
            current = await self.load_scan(scan_id)
            updated = mutate(current)
            updated.revision = current.revision + 1
            return await self.create_scan(updated)

    async def list_scans(self, *, source: str | None, offset: int, limit: int) -> dict[str, Any]:
        scans_dir = self.data_root / "scans"
        if not scans_dir.exists():
            return {"items": [], "total": 0, "offset": offset, "limit": limit}
        items = []
        for scan_dir in sorted(scans_dir.iterdir(), key=lambda p: p.name, reverse=True):
            if not scan_dir.is_dir():
                continue
            scan_file = scan_dir / "scan.json"
            if not scan_file.exists():
                continue
            try:
                doc = ScanDocument.model_validate(self._read_json(scan_file))
                if source is not None and doc.source != source:
                    continue
                severity_order = {"informational": 0, "low": 1, "medium": 2, "high": 3}
                highest = max((finding.severity for finding in doc.findings), key=severity_order.get, default=None)
                item = {
                    "scan_id": doc.scan_id,
                    "state": doc.state,
                    "source": doc.source,
                    "created_at": doc.created_at,
                    "device_count": len(doc.devices),
                    "finding_count": len(doc.findings),
                    "highest_severity": highest,
                    "storage_status": "ok",
                }
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
        return {"items": items[offset: offset + limit], "total": len(items), "offset": offset, "limit": limit}

    async def delete_scan(self, scan_id: UUID) -> None:
        scan_dir = self._scan_dir(scan_id)
        if scan_dir.exists():
            trash_dir = self.data_root / ".trash"
            trash_dir.mkdir(parents=True, exist_ok=True)
            os.rename(scan_dir, trash_dir / str(scan_id))

    async def export_scan(self, scan_id: UUID) -> ExportDocument:
        doc = await self.load_scan(scan_id)
        return ExportDocument(
            exported_at=doc.created_at,
            source=doc.source,
            coverage={"candidate_count": doc.coverage.candidate_count, "discovered_count": doc.coverage.discovered_count},
            devices=[{"device_id": d.device_id, "ip": "device-001"} for d in doc.devices],
            findings=[{"finding_id": f.finding_id, "rule_id": f.rule_id, "severity": f.severity} for f in doc.findings],
        )

    async def load_settings(self) -> Settings:
        settings_file = self.data_root / "settings.json"
        if not settings_file.exists():
            return Settings()
        return Settings.model_validate(self._read_json(settings_file))

    async def update_settings(self, update: SettingsUpdate, expected_revision: int) -> Settings:
        settings = await self.load_settings()
        if settings.revision != expected_revision:
            raise ValueError("revision conflict")
        for field, value in update.model_dump(exclude={"expected_revision"}, exclude_none=True).items():
            setattr(settings, field, value)
        settings.revision += 1
        path = self.data_root / "settings.json"
        payload = json.dumps(settings.model_dump(mode="json"), ensure_ascii=False, allow_nan=False)
        self._atomic_write(path, payload, self.data_root / "settings.previous.json")
        return settings
