"""All removal tests use isolated synthetic reports; no scanner is executed."""

import asyncio
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.jobs.supervisor import ScanSupervisor
from app.main import create_app
from app.schemas.report_management import (
    ReportDeleteRequest,
    ReportDeleteTarget,
    ReportRestoreRequest,
)
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import AnnotationStore, TitleUpdate
from app.storage.json_store import JsonStore
from app.storage.library import search_reports
from app.storage.report_trash import ReportTrash
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.session_helpers import BASE_URL, authenticate_client


def saved_report(store, **changes):
    document = ScanDocument(
        scan_id=str(uuid4()),
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
        policy={"profile": "light", "allowed_network": "192.168.56.0/24"},
    ).model_copy(update=changes)
    return store._create_scan(document)


def target(document, notes_revision=1):
    return ReportDeleteTarget(
        scan_id=document.scan_id,
        expected_revision=document.revision,
        expected_notes_revision=notes_revision,
    )


def test_delete_and_undo_preserve_all_evidence_notes_and_global_files(tmp_path):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    notes = AnnotationStore(store)._update(
        document.scan_id, title=TitleUpdate(expected_revision=1, title="Synthetic review")
    )
    store._save_raw_output(document.scan_id, "discovery.xml", b"<synthetic />")
    folder = store._scan_dir(document.scan_id)
    store._atomic_write(folder / "guidance" / "saved.json", '{"synthetic":true}')
    for name in ("nicknames.json", "settings.json"):
        store._atomic_write(tmp_path / name, '{"synthetic_global":true}')
    original = {
        str(path.relative_to(folder)): path.read_bytes()
        for path in folder.rglob("*")
        if path.is_file()
    }
    assert search_reports(store)["total"] == 1
    assert document.scan_id in store.library_cache.entries

    trash = ReportTrash(store)
    receipt = trash._delete(target(document, notes.revision))
    assert receipt["status"] == "deleted"
    assert not folder.exists()
    assert search_reports(store)["total"] == 0
    assert document.scan_id not in store.library_cache.entries
    archive = tmp_path / ".trash" / receipt["trash_id"]
    for name, contents in original.items():
        assert (archive / name).read_bytes() == contents
    for name in ("nicknames.json", "settings.json"):
        assert (tmp_path / name).read_text() == '{"synthetic_global":true}'

    restored = trash._restore(receipt["trash_id"])
    assert restored["status"] == "restored"
    assert restored["scan_id"] == document.scan_id
    assert not archive.exists()
    for name, contents in original.items():
        assert (folder / name).read_bytes() == contents
    assert search_reports(store)["total"] == 1
    assert trash._restore(receipt["trash_id"])["status"] == "missing"


@pytest.mark.parametrize("changed", ["evidence", "notes"])
def test_changed_report_or_notes_are_not_removed(tmp_path, changed):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    request = target(document)
    if changed == "evidence":
        store._update_scan(document.scan_id, lambda current: current, document.revision)
    else:
        AnnotationStore(store)._update(
            document.scan_id, title=TitleUpdate(expected_revision=1, title="New title")
        )
    assert ReportTrash(store)._delete(request)["status"] == "changed"
    assert store._scan_dir(document.scan_id).is_dir()
    assert not (tmp_path / ".trash").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "queued", "phase": "queued"},
        {"state": "running", "phase": "service_scan"},
        {"state": "running", "phase": "analysis", "analysis_status": "running"},
        {"state": "completed", "phase": "finished", "analysis_status": "running"},
    ],
)
def test_unfinished_documents_are_never_removed(tmp_path, changes):
    store = JsonStore(tmp_path)
    document = saved_report(store, **changes)
    assert ReportTrash(store)._delete(target(document))["status"] == "active"
    assert store._scan_dir(document.scan_id).is_dir()


def test_missing_and_unreadable_reports_are_distinguished_without_erasure(tmp_path):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    absent = target(document).model_copy(update={"scan_id": str(uuid4())})
    trash = ReportTrash(store)
    assert trash._delete(absent)["status"] == "missing"
    scan = store._scan_dir(document.scan_id) / "scan.json"
    store._atomic_write(scan, "synthetic corruption")
    assert trash._delete(target(document))["status"] == "unavailable"
    assert scan.read_text() == "synthetic corruption"
    assert not (tmp_path / ".trash").exists()


def test_corrupt_or_missing_notes_with_recovery_material_are_not_reset(tmp_path):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    folder = store._scan_dir(document.scan_id)
    store._atomic_write(folder / "annotations.previous.json", '{"revision":8}')
    original = (folder / "scan.json").read_bytes()
    assert ReportTrash(store)._delete(target(document))["status"] == "unavailable"
    assert not (folder / "annotations.json").exists()
    assert (folder / "scan.json").read_bytes() == original
    store._atomic_write(folder / "annotations.json", "synthetic corrupt notes")
    assert ReportTrash(store)._delete(target(document))["status"] == "unavailable"
    assert (folder / "annotations.json").read_text() == "synthetic corrupt notes"


def test_rename_failure_preserves_factual_files_and_reports_no_success(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    scan = store._scan_dir(document.scan_id) / "scan.json"
    original = scan.read_bytes()

    def fail_move(*_args):
        raise PermissionError("A private local path must not enter the response")

    monkeypatch.setattr("app.storage.report_trash.os.rename", fail_move)
    result = ReportTrash(store)._delete(target(document))
    assert result["status"] == "unavailable"
    assert "private" not in result["message"]
    assert scan.read_bytes() == original
    assert list((tmp_path / ".trash").iterdir()) == []


def test_post_move_cache_failure_cannot_report_false_failed_deletion(tmp_path):
    store = JsonStore(tmp_path)
    document = saved_report(store)

    class BrokenCacheLock:
        def __enter__(self):
            raise OSError("Synthetic cache housekeeping failure")

        def __exit__(self, *_args):
            return False

    store.library_cache.lock = BrokenCacheLock()
    receipt = ReportTrash(store)._delete(target(document))
    assert receipt["status"] == "deleted"
    assert not store._scan_dir(document.scan_id).exists()
    assert (tmp_path / ".trash" / receipt["trash_id"] / "scan.json").is_file()


def test_terminal_sidecar_survives_delete_and_undo(tmp_path):
    store = JsonStore(tmp_path)
    document = saved_report(store, state="running", phase="analysis", analysis_status="running")
    store._atomic_write(
        store._scan_dir(document.scan_id) / "terminal.json",
        json.dumps(
            {
                "scan_id": document.scan_id,
                "base_revision": document.revision,
                "updates": {"state": "failed", "phase": "finished", "analysis_status": "failed"},
            }
        ),
    )
    saved = store._load_scan(document.scan_id)
    assert saved.phase == "finished"
    trash = ReportTrash(store)
    receipt = trash._delete(target(saved))
    assert receipt["status"] == "deleted"
    assert trash._restore(receipt["trash_id"])["status"] == "restored"
    restored = store._load_scan(document.scan_id)
    assert restored.state == "failed" and restored.phase == "finished"


@pytest.mark.parametrize("limit", ["reports", "bytes", "deadline"])
def test_full_archive_and_expired_deadline_fail_closed(tmp_path, limit):
    store = JsonStore(tmp_path)
    first, second = saved_report(store), saved_report(store)
    trash = ReportTrash(store)
    kwargs = {}
    if limit == "reports":
        assert trash._delete(target(first))["status"] == "deleted"
        trash.max_reports = 1
    elif limit == "bytes":
        trash.max_bytes = 1
    else:
        kwargs["deadline"] = time.monotonic() - 1
    result = trash._delete(target(second), **kwargs)
    assert result["status"] == "unavailable"
    assert store._scan_dir(second.scan_id).is_dir()


def test_existing_report_lock_blocks_remove_without_racing_writer(tmp_path):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    store.lock_timeout_s = 0.01
    with store._scan_lock(document.scan_id):
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = executor.submit(ReportTrash(store)._delete, target(document)).result(timeout=3)
    assert result["status"] == "unavailable"
    assert store._scan_dir(document.scan_id).exists()


def test_undo_never_overwrites_an_existing_report(tmp_path):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    trash = ReportTrash(store)
    receipt = trash._delete(target(document))
    replacement = document.model_copy(update={"revision": 10})
    store._create_scan(replacement)
    original = (store._scan_dir(document.scan_id) / "scan.json").read_bytes()
    assert trash._restore(receipt["trash_id"])["status"] == "changed"
    assert (store._scan_dir(document.scan_id) / "scan.json").read_bytes() == original
    assert (tmp_path / ".trash" / receipt["trash_id"]).is_dir()


@pytest.mark.parametrize("tamper", ["report_revision", "notes_revision", "receipt", "state"])
def test_undo_rejects_changed_or_wrong_recovery_copy(tmp_path, tamper):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    trash = ReportTrash(store)
    receipt = trash._delete(target(document))
    archive = tmp_path / ".trash" / receipt["trash_id"]
    if tamper == "notes_revision":
        store._atomic_write(archive / "annotations.json", '{"revision":7}')
    else:
        path = archive / (".removal-receipt.json" if tamper == "receipt" else "scan.json")
        payload = json.loads(path.read_text())
        if tamper == "receipt":
            payload["trash_id"] = str(uuid4())
        elif tamper == "state":
            payload.update(state="running", phase="analysis", analysis_status="running")
        else:
            payload["revision"] += 1
        store._atomic_write(path, json.dumps(payload))
    assert trash._restore(receipt["trash_id"])["status"] in {"changed", "unavailable"}
    assert archive.is_dir()
    assert not store._scan_dir(document.scan_id).exists()


@pytest.mark.parametrize("location", ["scans", "report", "nested", "trash", "receipt"])
def test_links_never_redirect_deletion_or_undo_outside_managed_root(tmp_path, location):
    store = JsonStore(tmp_path / "managed")
    document = saved_report(store)
    folder = store._scan_dir(document.scan_id)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "evidence.json"
    sentinel.write_text("synthetic outside evidence", encoding="utf-8")
    trash = ReportTrash(store)
    receipt = trash._delete(target(document)) if location == "receipt" else None
    if location == "scans":
        # Recoverably move the synthetic parent before replacing it with a link.
        os.rename(store.data_root / "scans", store.data_root / "original-scans")
        link = store.data_root / "scans"
    elif location == "report":
        os.rename(folder, store.data_root / "original-report")
        link = folder
    elif location == "nested":
        link = folder / "linked-evidence"
    elif location == "receipt":
        link = store.data_root / ".trash" / receipt["trash_id"] / ".removal-receipt.json"
        link.unlink()
    else:
        link = store.data_root / ".trash"
    try:
        link.symlink_to(
            sentinel if location == "receipt" else outside,
            target_is_directory=location != "receipt",
        )
    except OSError as exc:
        pytest.skip(f"Symbolic link creation is unavailable on this host: {exc}")
    result = trash._restore(receipt["trash_id"]) if receipt else trash._delete(target(document))
    assert result["status"] == "unavailable"
    assert sentinel.read_text() == "synthetic outside evidence"
    assert link.is_symlink()


@pytest.mark.parametrize("location", ["scans", "locks", "report", "nested", "trash"])
def test_windows_junction_guard_runs_without_link_creation_privilege(
    tmp_path, monkeypatch, location
):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    folder = store._scan_dir(document.scan_id)
    junction = {
        "scans": tmp_path / "scans",
        "locks": tmp_path / "locks",
        "report": folder,
        "nested": folder / "simulated-junction",
        "trash": tmp_path / ".trash",
    }[location]
    if location == "nested":
        junction.mkdir()
    actual = getattr(Path, "is_junction", lambda path: False)
    monkeypatch.setattr(
        Path, "is_junction", lambda path: path == junction or actual(path), raising=False
    )
    result = ReportTrash(store)._delete(target(document))
    assert result["status"] == "unavailable"
    assert (folder / "scan.json").is_file()


def test_deletion_and_undo_work_without_newer_pathlib_junction_method(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    monkeypatch.delattr(Path, "is_junction", raising=False)
    trash = ReportTrash(store)
    receipt = trash._delete(target(document))
    assert receipt["status"] == "deleted"
    assert trash._restore(receipt["trash_id"])["status"] == "restored"
    assert store._scan_dir(document.scan_id).exists()


def test_older_pathlib_still_rejects_windows_mount_point_tag(tmp_path, monkeypatch):
    from app.storage.report_trash import UnsafeReportPath

    store = JsonStore(tmp_path)
    document = saved_report(store)
    folder = store._scan_dir(document.scan_id)
    monkeypatch.delattr(Path, "is_junction", raising=False)
    # Inspect the compatibility branch directly, without creating a privileged link.
    mode = folder.stat().st_mode
    monkeypatch.setattr(
        "app.storage.report_trash.stat.IO_REPARSE_TAG_MOUNT_POINT", 123, raising=False
    )
    monkeypatch.setattr(
        Path, "lstat", lambda path: SimpleNamespace(st_reparse_tag=123, st_mode=mode)
    )
    with pytest.raises(UnsafeReportPath):
        ReportTrash(store)._safe_path(folder)


@pytest.mark.parametrize(
    "update",
    [
        {"scan_id": "../outside"},
        {"scan_id": "{aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa}"},
        {"scan_id": "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA"},
        {"expected_revision": 0},
        {"expected_revision": True},
        {"expected_notes_revision": "1"},
    ],
)
def test_delete_request_rejects_noncanonical_paths_and_revisions(update):
    payload = {
        "scan_id": str(uuid4()),
        "expected_revision": 1,
        "expected_notes_revision": 1,
        **update,
    }
    with pytest.raises(ValidationError):
        ReportDeleteRequest(reports=[payload])


def test_request_batches_are_bounded_and_unique():
    one = {"scan_id": str(uuid4()), "expected_revision": 1, "expected_notes_revision": 1}
    for reports in ([], [one, one], [{**one, "scan_id": str(uuid4())} for _ in range(25)]):
        with pytest.raises(ValidationError):
            ReportDeleteRequest(reports=reports)
    trash_id = str(uuid4())
    for ids in ([], [trash_id, trash_id], [str(uuid4()) for _ in range(25)], ["../outside"]):
        with pytest.raises(ValidationError):
            ReportRestoreRequest(trash_ids=ids)


@pytest.mark.asyncio
async def test_active_ai_retry_is_not_removed_and_batch_preserves_other_outcomes(tmp_path):
    store = JsonStore(tmp_path)
    active, good, changed = (saved_report(store) for _ in range(3))
    supervisor = ScanSupervisor(store)
    blocker = asyncio.create_task(asyncio.Event().wait())
    supervisor._analysis_tasks[active.scan_id] = blocker
    store._update_scan(changed.scan_id, lambda document: document, changed.revision)
    try:
        results = await supervisor.delete_reports([target(active), target(good), target(changed)])
        assert [item["status"] for item in results] == ["active", "deleted", "changed"]
        assert store._scan_dir(active.scan_id).exists()
        assert store._scan_dir(changed.scan_id).exists()
        assert not store._scan_dir(good.scan_id).exists()
    finally:
        blocker.cancel()
        await asyncio.gather(blocker, return_exceptions=True)


@pytest.mark.asyncio
async def test_cancellation_keeps_admission_locked_until_worker_finishes(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    document = saved_report(store)
    supervisor = ScanSupervisor(store)
    worker_started = threading.Event()
    worker_release = threading.Event()
    original_delete = ReportTrash._delete

    def held_delete(self, item, **kwargs):
        worker_started.set()
        if not worker_release.wait(timeout=3):
            raise AssertionError("Synthetic removal worker was not released")
        return original_delete(self, item, **kwargs)

    monkeypatch.setattr(ReportTrash, "_delete", held_delete)
    deletion = asyncio.create_task(supervisor.delete_reports([target(document)]))
    try:
        assert await asyncio.to_thread(worker_started.wait, 2)
        deletion.cancel()
        retry = asyncio.create_task(supervisor.request_explanations(document.scan_id))
        await asyncio.sleep(0)
        assert supervisor._admission.locked()
        assert not deletion.done()
        assert not retry.done()
        worker_release.set()
        with pytest.raises(asyncio.CancelledError):
            await deletion
        with pytest.raises(FileNotFoundError):
            await retry
        assert not store._scan_dir(document.scan_id).exists()
    finally:
        worker_release.set()
        await asyncio.gather(deletion, return_exceptions=True)


def test_report_management_api_requires_session_csrf_and_validated_bodies():
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        document = saved_report(client.app.state.store)
        body = {"reports": [target(document).model_dump()]}
        assert client.post("/api/reports/delete", json=body).status_code == 403
        assert (
            client.post("/api/reports/restore", json={"trash_ids": [str(uuid4())]}).status_code
            == 403
        )
        headers = authenticate_client(client, manager)
        assert client.post("/api/reports/delete", json=body).status_code == 403
        assert (
            client.post("/api/reports/restore", json={"trash_ids": [str(uuid4())]}).status_code
            == 403
        )
        assert (
            client.post("/api/reports/delete", json={"reports": []}, headers=headers).status_code
            == 422
        )
        response = client.post("/api/reports/delete", json=body, headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert payload["deleted_count"] == 1 and payload["recoverable"] is True
        assert client.get(f"/api/live-scans/{document.scan_id}").status_code == 404
        restored = client.post(
            "/api/reports/restore",
            headers=headers,
            json={"trash_ids": [payload["results"][0]["trash_id"]]},
        )
        assert restored.status_code == 200
        assert restored.json()["restored_count"] == 1
        assert client.get(f"/api/live-scans/{document.scan_id}").status_code == 200
