import json
from uuid import uuid4

import pytest
from app.schemas.scan import Device, ScanDocument
from app.storage.json_store import JsonStore
from app.storage.maintenance import maintain
from filelock import FileLock, Timeout


def make_report(root, **changes):
    store = JsonStore(root)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "demo", "hosts": []},
        state="completed",
        phase="finished",
        created_at="2000-01-01T00:00:00Z",
    ).model_copy(update=changes)
    store._create_scan(doc)
    store._update_scan(doc.scan_id, lambda current: current, None)
    return store, doc


def test_recovery_preview_and_apply_preserve_original_files(tmp_path):
    store, doc = make_report(tmp_path)
    folder = tmp_path / "scans" / doc.scan_id
    primary = folder / "scan.json"
    primary.write_text("invalid checkpoint", encoding="utf-8")
    before = {path.name: path.read_bytes() for path in folder.iterdir() if path.is_file()}
    preview = maintain(tmp_path, "recover", scan_id=doc.scan_id)
    assert not preview["applied"]
    assert len(list((tmp_path / "scans").iterdir())) == 1
    result = maintain(tmp_path, "recover", scan_id=doc.scan_id, apply=True)
    assert result["applied"]
    recovered = store._load_scan(result["recovered_scan_id"])
    assert recovered.state == "completed"
    assert recovered.warnings[-1]["code"] == "RECOVERED_CHECKPOINT"
    assert recovered.devices == doc.devices
    assert before == {path.name: path.read_bytes() for path in folder.iterdir() if path.is_file()}


def test_retention_is_preview_and_excludes_failed_active_and_unreadable(tmp_path):
    _, complete = make_report(tmp_path)
    make_report(tmp_path, state="failed")
    make_report(tmp_path, state="running", phase="service_scan")
    _, broken = make_report(tmp_path)
    (tmp_path / "scans" / broken.scan_id / "scan.json").write_text("broken", encoding="utf-8")
    result = maintain(tmp_path, "retention", older_than_days=90)
    assert [item["scan_id"] for item in result["items"]] == [complete.scan_id]
    assert len(list((tmp_path / "scans").iterdir())) == 4
    with pytest.raises(ValueError, match="preview"):
        maintain(tmp_path, "retention", apply=True)


def test_maintenance_cannot_run_while_application_owns_storage(tmp_path):
    with FileLock(str(tmp_path / "app-instance.lock")):
        with pytest.raises(Timeout):
            maintain(tmp_path, "audit")


def test_backup_with_wrong_id_cannot_be_recovered(tmp_path):
    _, doc = make_report(tmp_path)
    backup = tmp_path / "scans" / doc.scan_id / "scan.previous.json"
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["scan_id"] = str(uuid4())
    backup.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="Backup ID"):
        maintain(tmp_path, "recover", scan_id=doc.scan_id, apply=True)


def test_backup_recovery_never_revives_an_interrupted_job(tmp_path):
    store, doc = make_report(tmp_path, state="running", phase="service_scan")
    result = maintain(tmp_path, "recover", scan_id=doc.scan_id, apply=True)
    recovered = store._load_scan(result["recovered_scan_id"])
    assert recovered.phase == "finished"
    assert recovered.state == "failed"
    assert recovered.coverage.service_completed_count == 0


def test_recovered_devices_belong_to_the_new_report(tmp_path):
    store, doc = make_report(tmp_path)
    device = Device(device_id="device", scan_id=doc.scan_id, ip="192.168.0.2")
    store._update_scan(
        doc.scan_id, lambda current: current.model_copy(update={"devices": [device]}), None
    )
    store._update_scan(doc.scan_id, lambda current: current, None)
    result = maintain(tmp_path, "recover", scan_id=doc.scan_id, apply=True)
    recovered = store._load_scan(result["recovered_scan_id"])
    assert recovered.devices[0].scan_id == recovered.scan_id
    assert recovered.devices[0].device_id == device.device_id
    assert store._load_scan(doc.scan_id).devices[0].scan_id == doc.scan_id
