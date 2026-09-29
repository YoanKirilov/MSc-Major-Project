"""Restore drill using an isolated COPY of one explicit report, never live storage."""

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from uuid import UUID

from app.schemas.scan import ScanDocument
from app.storage.json_store import JsonStore
from app.storage.maintenance import maintain


def fingerprints(folder):
    return {
        str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in folder.rglob("*")
        if p.is_file()
    }


def check_restore(data_dir, scan_id, artifacts):
    source = Path(data_dir).resolve(strict=True) / "scans" / str(UUID(scan_id))
    if not source.is_dir() or source.is_symlink():
        raise ValueError("Select an existing, non-linked report folder")
    if any(
        p.is_symlink() or getattr(p, "is_junction", lambda: False)()
        for p in [source, *source.rglob("*")]
    ):
        raise ValueError("Linked report content is not supported")
    before = fingerprints(source)
    backup = ScanDocument.model_validate_json((source / "scan.previous.json").read_bytes())
    artifacts = Path(artifacts).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    if artifacts.is_relative_to(source):
        raise ValueError("Artifacts must not be inside the original report")
    root = Path(tempfile.mkdtemp(prefix="restore-", dir=artifacts))
    copy = root / "scans" / source.name
    shutil.copytree(source, copy)
    # Deliberate corruption is confined to this newly created disposable COPY.
    (copy / "scan.json").write_text("synthetic interrupted write", encoding="utf-8")
    copied_before = fingerprints(copy)
    preview = maintain(root, "recover", scan_id=scan_id)
    assert not preview["applied"]
    result = maintain(root, "recover", scan_id=scan_id, apply=True)
    recovered = JsonStore(root)._load_scan(result["recovered_scan_id"])
    assert recovered.scan_id != scan_id
    assert recovered.services == backup.services and recovered.findings == backup.findings
    assert [d.model_dump(exclude={"scan_id"}) for d in recovered.devices] == [
        d.model_dump(exclude={"scan_id"}) for d in backup.devices
    ]
    assert recovered.phase == "finished" and recovered.state not in {"queued", "running"}
    assert recovered.warnings[-1]["code"] == "RECOVERED_CHECKPOINT"
    assert fingerprints(copy) == copied_before and fingerprints(source) == before
    summary = {
        "source_unchanged": True,
        "copied_evidence_unchanged": True,
        "backup_revision": backup.revision,
        "restored_state": recovered.state,
        "devices": len(recovered.devices),
        "findings": len(recovered.findings),
        "artifacts": str(root),
    }
    (root / "drill.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--scan-id", required=True)
    parser.add_argument("--artifacts", default=".test-artifacts")
    args = parser.parse_args()
    print(json.dumps(check_restore(args.data_dir, args.scan_id, args.artifacts), indent=2))
