"""Offline maintenance: preview retention and recover without overwriting evidence."""

import json
import re
import shutil
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4

from app.schemas.common import utc_now
from app.schemas.scan import GuidanceSnapshot, ScanDocument
from app.storage.json_store import JsonStore
from filelock import FileLock


def _managed(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("Managed path escapes the selected data folder")
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        raise ValueError("Linked storage paths are not supported for maintenance")
    return path


def _backup(store, folder):
    document = ScanDocument.model_validate(store._read_json(folder / "scan.previous.json"))
    if document.scan_id != folder.name:
        raise ValueError("Backup ID does not match its report folder")
    for name in document.guidance_archives:
        if not re.fullmatch(r"guidance-[0-9a-f-]{36}\.json", name):
            raise ValueError("Invalid guidance archive name")
        GuidanceSnapshot.model_validate(
            store._read_json(_managed(store.data_root.resolve(), folder / "guidance" / name))
        )
    return document


def maintain(data_dir, action, *, scan_id=None, older_than_days=90, apply=False):
    """Never start the backend or a scanner. Recovery creates a new report ID."""
    root = Path(data_dir).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Select an existing application data folder")
    if older_than_days < 1:
        raise ValueError("Retention age must be at least one day")
    with FileLock(str(root / "app-instance.lock"), timeout=0):
        store = JsonStore(root)
        scans = _managed(root, root / "scans")
        if action == "recover":
            folder = _managed(root, scans / str(UUID(str(scan_id))))
            document = _backup(store, folder)
            result = {
                "source_scan_id": document.scan_id,
                "backup_revision": document.revision,
                "applied": False,
                "note": "Recovery creates a separate report; original files remain unchanged.",
            }
            if not apply:
                return result
            # Validate all copied paths before creating a destination. Only referenced
            # guidance is copied; the original raw evidence stays with the source.
            if document.phase != "finished" or document.state in {"queued", "running"}:
                from app.jobs.supervisor import ScanSupervisor

                document = ScanSupervisor._interrupted_document(document)
            document.scan_id = str(uuid4())
            for device in document.devices:
                device.scan_id = document.scan_id
            document.revision = 1
            document.warnings.append(
                {
                    "code": "RECOVERED_CHECKPOINT",
                    "message": (
                        f"Recovered an older checkpoint of report {result['source_scan_id']}. "
                        "Later observations may be missing. "
                        "Original files and raw output were kept."
                    ),
                }
            )
            destination = _managed(root, scans / document.scan_id)
            for name in document.guidance_archives:
                target = destination / "guidance" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(folder / "guidance" / name, target)
            store._create_scan(document)
            return {**result, "applied": True, "recovered_scan_id": document.scan_id}
        if action not in {"audit", "retention"} or apply:
            raise ValueError("Only recovery supports --apply; retention is a preview")
        from datetime import datetime

        cutoff = utc_now() - timedelta(days=older_than_days)
        items = []
        for folder in sorted(scans.iterdir()) if scans.exists() else []:
            if not folder.is_dir():
                continue
            item = {"scan_id": folder.name, "status": "unreadable", "retention_candidate": False}
            try:
                _managed(root, folder)
                UUID(folder.name)
                document = store._load_scan(folder.name)
                item.update(status="ok", state=document.state, revision=document.revision)
                item["retention_candidate"] = (
                    document.state == "completed"
                    and document.phase == "finished"
                    and datetime.fromisoformat(document.created_at) < cutoff
                )
                for name in document.guidance_archives:
                    if not re.fullmatch(r"guidance-[0-9a-f-]{36}\.json", name):
                        raise ValueError("Invalid archive name")
                    GuidanceSnapshot.model_validate(
                        store._read_json(_managed(root, folder / "guidance" / name))
                    )
            except (OSError, ValueError, TypeError):
                item.update(status="unreadable", retention_candidate=False)
            try:
                _managed(root, folder)
                _backup(store, folder)
                item["backup_available"] = True
            except (OSError, ValueError, TypeError):
                item["backup_available"] = False
            items.append(item)
        return {
            "action": action,
            "applied": False,
            "older_than_days": older_than_days,
            "items": items if action == "audit" else [i for i in items if i["retention_candidate"]],
        }


def print_result(result):
    print(json.dumps(result, indent=2))
