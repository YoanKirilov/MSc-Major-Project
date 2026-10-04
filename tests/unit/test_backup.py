from uuid import uuid4

import pytest
from app.schemas.scan import ScanDocument
from app.storage.backup import storage_usage, transfer
from app.storage.json_store import JsonStore
from filelock import FileLock, Timeout


def test_export_restore_preserve_reports_and_exclude_secrets(tmp_path):
    source = tmp_path / "source"
    store = JsonStore(source)
    scan = ScanDocument(
        scan_id=str(uuid4()), target={"mode": "known_hosts", "hosts": ["192.168.0.2"]}
    )
    store._create_scan(scan)
    secret = source / "session-secret.txt"
    secret.write_text("do not copy", encoding="utf-8")
    original = (source / "scans" / scan.scan_id / "scan.json").read_bytes()
    backup = tmp_path / "backup"
    assert transfer(source, backup)["verified"]
    assert not (backup / secret.name).exists()
    restored = tmp_path / "restored"
    assert transfer(backup, restored, restore=True)["verified"]
    assert JsonStore(restored)._load_scan(scan.scan_id).scan_id == scan.scan_id
    assert (source / "scans" / scan.scan_id / "scan.json").read_bytes() == original
    assert storage_usage(source)["bytes"] > 0
    with pytest.raises(ValueError, match="new destination"):
        transfer(source, backup)
    (backup / "scans" / scan.scan_id / "scan.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        transfer(backup, tmp_path / "bad", restore=True)
    assert not (tmp_path / "bad").exists()


def test_export_refuses_active_source(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    with FileLock(str(source / "app-instance.lock")):
        with pytest.raises(Timeout):
            transfer(source, tmp_path / "backup")
