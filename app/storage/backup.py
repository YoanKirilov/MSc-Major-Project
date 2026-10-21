"""Offline, checksum-verified folder backups. Never replace or delete source data."""

import hashlib
import json
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

from app.storage.maintenance import _managed
from app.storage.report_trash import ReportTrash
from filelock import FileLock

MAX_BACKUP_BYTES = 3 * 1024 * 1024 * 1024
MAX_FILES = 20000
ALLOWED = re.compile(
    # Removed periodic-check settings are archival data only. Preserve them in
    # private backups; the app has no scheduler or reader that can execute them.
    r"(?:settings|nicknames|device-labels|monitor)(?:\.previous)?\.json|nicknames\.recovery\.json|"
    r"nicknames\.corrupt-[0-9a-f]{32}\.json|"
    r"(?:scans|\.trash)/[0-9a-f-]{36}/(?:[a-z.]+\.json|\.removal-receipt\.json|annotations\.corrupt-[0-9a-f]{32}\.json|"
    r"raw/[a-zA-Z0-9.-]+\.xml|guidance/guidance-[0-9a-f-]{36}\.json)"
)


def files_to_backup(root):
    root = Path(root).resolve(strict=True)
    files = []
    total = 0
    safety = ReportTrash(SimpleNamespace(data_root=root))

    def walk(folder):
        pending = [folder]
        count = 0
        while pending:
            parent = pending.pop()
            safety._safe_path(parent)
            for entry in parent.iterdir():
                count += 1
                if count > 100000:
                    raise ValueError("Backup exceeds its bounded entry policy")
                safety._safe_path(entry)
                if entry.is_dir():
                    pending.append(entry)
                else:
                    yield entry

    for path in root.iterdir():
        if path.name in {"scans", ".trash"}:
            _managed(root, path)
            candidates = walk(path)
        elif path.name in {
            "settings.json",
            "settings.previous.json",
            "nicknames.json",
            "nicknames.previous.json",
            "nicknames.recovery.json",
            "device-labels.json",
            "device-labels.previous.json",
            "monitor.json",
            "monitor.previous.json",
        } or re.fullmatch(r"nicknames\.corrupt-[0-9a-f]{32}\.json", path.name):
            candidates = [path]
        else:
            continue
        for entry in candidates:
            safety._safe_path(entry)
            _managed(root, entry)
            if not entry.is_file():
                continue
            relative = entry.relative_to(root).as_posix()
            if not ALLOWED.fullmatch(relative):
                continue
            size = entry.stat().st_size
            total += size
            if size > 20 * 1024 * 1024 or total > MAX_BACKUP_BYTES or len(files) >= MAX_FILES:
                raise ValueError("Backup exceeds its bounded file/size policy")
            files.append((relative, entry, size))
    return files, total


def storage_usage(root):
    files, total = files_to_backup(root)
    recovery = [item for item in files if item[0].startswith(".trash/")]
    recovery_bytes = sum(item[2] for item in recovery)
    recovery_reports = sum(item[0].endswith("/.removal-receipt.json") for item in recovery)
    near_limit = (
        recovery_bytes >= ReportTrash.max_bytes * 0.8
        or recovery_reports >= ReportTrash.max_reports * 0.8
    )
    return {
        "bytes": total,
        "files": len(files),
        "active_bytes": total - recovery_bytes,
        "recovery_bytes": recovery_bytes,
        "recovery_files": len(recovery),
        "recovery_limit_bytes": ReportTrash.max_bytes,
        "recovery_reports": recovery_reports,
        "recovery_limit_reports": ReportTrash.max_reports,
        "recovery_near_limit": near_limit,
        "warning": (
            "Recovery storage is nearing its capacity. Back up privately before further deletion; "
            "deleting keeps recovery copies and does not free space. No files were removed."
        )
        if near_limit
        else "Consider an offline backup and review older reports."
        if total >= 250 * 1024 * 1024
        else None,
    }


def transfer(data_dir, destination, *, restore=False):
    """Source must be idle; destination must be new. Failure never removes evidence."""
    source = Path(data_dir).resolve(strict=True)
    target = Path(destination).resolve()
    if target.exists() or target == source or target.is_relative_to(source):
        raise ValueError("Choose a new destination folder outside the source data folder")
    with FileLock(str(source / "app-instance.lock"), timeout=0):
        files, total = files_to_backup(source)
        manifest = {}
        for relative, path, size in files:
            manifest[relative] = {
                "bytes": size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        if restore:
            manifest_path = _managed(source, source / "backup-manifest.json")
            if manifest_path.stat().st_size > 5_000_000:
                raise ValueError("Backup manifest is too large")
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            if saved.get("format") != 1 or saved.get("files") != manifest:
                raise ValueError("Backup checksum verification failed; no destination was created")
        if not manifest:
            raise ValueError("No managed live-report data found")
        target.mkdir(parents=True, exist_ok=False)
        for relative, path, _ in files:
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, output)
            if hashlib.sha256(output.read_bytes()).hexdigest() != manifest[relative]["sha256"]:
                raise ValueError(
                    "Backup copy verification failed; preserve the source "
                    "and inspect the partial destination"
                )
        with (target / "backup-manifest.json").open("x", encoding="utf-8") as handle:
            json.dump({"format": 1, "files": manifest}, handle, indent=2)
        return {
            "destination": str(target),
            "files": len(files),
            "bytes": total,
            "verified": True,
            "note": (
                "Live reports/settings/nicknames/household labels and recovery copies copied. "
                "Demo runs, session secrets and locks "
                "excluded. Source unchanged apart from its instance lock."
            ),
        }
