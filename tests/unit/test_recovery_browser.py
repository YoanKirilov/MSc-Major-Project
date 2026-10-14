"""Read-only listing and complete backups use isolated synthetic storage only."""

import json
from uuid import uuid4

import pytest
from app.storage.annotations import AnnotationStore, TitleUpdate
from app.storage.backup import storage_usage, transfer
from app.storage.json_store import JsonStore
from app.storage.report_trash import ReportTrash
from tests.unit.test_report_trash import saved_report, target


def test_recovery_index_requires_session_and_enforces_page_bounds():
    from app.main import create_app
    from app.security.session import SessionManager
    from fastapi.testclient import TestClient
    from tests.session_helpers import BASE_URL, authenticate_client

    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        assert client.get("/api/reports/recovery").status_code == 401
        authenticate_client(client, manager)
        assert client.get("/api/report-capabilities").json()["management_version"] == 2
        assert client.get("/api/reports/recovery?limit=25").status_code == 422
        assert client.get("/api/reports/recovery?offset=-1").status_code == 422
        assert client.get("/api/reports/recovery").json()["items"] == []


def test_recovery_lists_metadata_with_bounded_pages_and_preserves_original_data(tmp_path):
    store = JsonStore(tmp_path)
    trash = ReportTrash(store)
    ids = []
    for index in range(26):
        doc = saved_report(store)
        notes = AnnotationStore(store)._update(
            doc.scan_id, title=TitleUpdate(expected_revision=1, title=f"Saved {index}")
        )
        ids.append(trash._delete(target(doc, notes.revision))["trash_id"])
    page = trash.list_reports()
    assert page["total"] == 26 and len(page["items"]) == 24
    assert all(item["restorable"] and item["bytes"] > 0 for item in page["items"])
    assert len(trash.list_reports(offset=24)["items"]) == 2
    assert all(item["target"]["hosts"] == ["192.168.56.10"] for item in page["items"])
    restored = trash._restore(ids[0])
    assert restored["status"] == "restored"
    assert trash.list_reports()["total"] == 25


def test_recovery_preserves_damaged_receipts_and_refuses_changed_copies(tmp_path):
    store = JsonStore(tmp_path)
    trash = ReportTrash(store)
    doc = saved_report(store)
    receipt = trash._delete(target(doc))
    folder = tmp_path / ".trash" / receipt["trash_id"]
    primary = folder / "scan.json"
    content = json.loads(primary.read_text())
    content["revision"] += 1
    primary.write_text(json.dumps(content), encoding="utf-8")
    assert trash.list_reports()["items"][0]["restorable"] is False
    assert trash._restore(receipt["trash_id"])["status"] == "changed"
    bad = tmp_path / ".trash" / str(uuid4())
    bad.mkdir()
    (bad / ".removal-receipt.json").write_text("bad", encoding="utf-8")
    page = trash.list_reports()
    assert page["total"] == 1 and page["warnings"]
    assert (bad / ".removal-receipt.json").read_text() == "bad"


def test_backup_and_usage_include_recovery_evidence_and_receipts(tmp_path):
    store = JsonStore(tmp_path / "source")
    doc = saved_report(store)
    trash = ReportTrash(store)
    receipt = trash._delete(target(doc))
    usage = storage_usage(store.data_root)
    assert usage["bytes"] == usage["active_bytes"] + usage["recovery_bytes"]
    assert usage["recovery_bytes"] > 0
    backup = tmp_path / "backup"
    transfer(store.data_root, backup)
    archive = backup / ".trash" / receipt["trash_id"]
    assert (archive / ".removal-receipt.json").exists()
    assert (archive / "scan.json").read_bytes() == (
        store.data_root / ".trash" / receipt["trash_id"] / "scan.json"
    ).read_bytes()
    restored = tmp_path / "restored"
    transfer(backup, restored, restore=True)
    restored_store = JsonStore(restored)
    assert ReportTrash(restored_store).list_reports()["items"][0]["restorable"]
    assert ReportTrash(restored_store)._restore(receipt["trash_id"])["status"] == "restored"


def test_recovery_scan_is_bounded_and_fail_closed_for_linked_paths(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    trash = ReportTrash(store)
    doc = saved_report(store)
    receipt = trash._delete(target(doc))
    unsafe = tmp_path / ".trash" / receipt["trash_id"]
    monkeypatch.setattr(type(unsafe), "is_symlink", lambda self: self == unsafe)
    page = trash.list_reports()
    assert page["total"] == 0 and page["warnings"]
    with pytest.raises(ValueError):
        storage_usage(tmp_path)
    assert unsafe.exists()
