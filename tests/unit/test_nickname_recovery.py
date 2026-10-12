"""Recovery and API failure boundaries using isolated JSON data only."""

import errno
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from app.main import create_app
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from app.storage.nicknames import NicknameStore, NicknameUpdate
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client
from tests.unit.test_nicknames import document


def saved_names(tmp_path):
    store = JsonStore(tmp_path)
    doc = document()
    store._create_scan(doc)
    names = NicknameStore(store)
    for revision, label in ((1, "TV"), (2, "Room TV")):
        names._update(
            doc,
            doc.devices[0].device_id,
            NicknameUpdate(expected_revision=revision, nickname=label),
        )
    return store, doc, names


@pytest.mark.parametrize("missing", [False, True])
def test_backup_recovery_preserves_evidence_and_invalidates_lost_revision(tmp_path, missing):
    store, doc, names = saved_names(tmp_path)
    evidence = (store._scan_dir(doc.scan_id) / "scan.json").read_bytes()
    backup = names.path.with_name("nicknames.previous.json").read_bytes()
    if missing:
        names.path.unlink()
    else:
        store._atomic_write(names.path, "invalid synthetic JSON")
    result = names._snapshot(doc, 3)
    assert result["revision"] == 4 and result["changed"]
    assert result["names"] == {doc.devices[0].device_id: "TV"}
    assert "latest edits may be missing" in result["recovery_notice"]
    assert names.path.with_name("nicknames.previous.json").read_bytes() == backup
    assert (store._scan_dir(doc.scan_id) / "scan.json").read_bytes() == evidence
    assert len(list(tmp_path.glob("nicknames.corrupt-*.json"))) == (0 if missing else 1)
    with pytest.raises(ValueError, match="changed"):
        names._update(
            doc, doc.devices[0].device_id, NicknameUpdate(expected_revision=3, nickname="stale")
        )
    names._update(
        doc, doc.devices[0].device_id, NicknameUpdate(expected_revision=4, nickname="Recovered TV")
    )
    assert names._snapshot(doc, 5)["recovery_notice"] == result["recovery_notice"]


@pytest.mark.parametrize(
    "case", ["both_invalid", "oversized_primary", "oversized_backup", "directory"]
)
def test_unsafe_or_invalid_data_is_not_silently_reset(tmp_path, case):
    store, doc, names = saved_names(tmp_path)
    backup = names.path.with_name("nicknames.previous.json")
    store._atomic_write(names.path, "invalid primary")
    if case == "both_invalid":
        store._atomic_write(backup, "invalid backup")
    elif case == "oversized_primary":
        store.max_document_bytes = 5
    elif case == "oversized_backup":
        store.max_document_bytes = names.path.stat().st_size
    else:
        names.path.unlink()
        names.path.mkdir()
    before = backup.read_bytes()
    with pytest.raises(ValueError):
        names._snapshot(doc, None)
    assert backup.read_bytes() == before
    assert (
        names.path.is_dir()
        if case == "directory"
        else names.path.read_bytes() == b"invalid primary"
    )
    assert not list(tmp_path.glob("nicknames.corrupt-*.json"))


def test_recovery_write_failure_keeps_primary_and_backup(tmp_path, monkeypatch):
    store, doc, names = saved_names(tmp_path)
    store._atomic_write(names.path, "invalid primary")
    backup = names.path.with_name("nicknames.previous.json").read_bytes()

    def fail(*args, **kwargs):
        raise OSError(errno.ENOSPC, "synthetic full disk")

    monkeypatch.setattr(store, "_atomic_write", fail)
    with pytest.raises(OSError):
        names._snapshot(doc, None)
    assert names.path.read_text() == "invalid primary"
    assert names.path.with_name("nicknames.previous.json").read_bytes() == backup


def test_concurrent_recovery_and_revision_checked_writers(tmp_path):
    store, doc, names = saved_names(tmp_path)
    store._atomic_write(names.path, "invalid primary")

    def read(_):
        return NicknameStore(store)._snapshot(doc, None)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(read, range(8)))
    assert all(result == results[0] for result in results)
    assert len(list(tmp_path.glob("nicknames.corrupt-*.json"))) == 1

    def edit(label):
        try:
            return NicknameStore(store)._update(
                doc, doc.devices[0].device_id, NicknameUpdate(expected_revision=4, nickname=label)
            )
        except ValueError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, ["TV A", "TV B"]))
    assert sorted(map(str, results)) == ["5", "conflict"]


def test_repeated_recovery_never_reuses_revision_of_a_stale_editor(tmp_path):
    store, doc, names = saved_names(tmp_path)
    store._atomic_write(names.path, "first corruption")
    first = names._snapshot(doc, None)
    store._atomic_write(names.path, "second corruption before any edit")
    second = names._snapshot(doc, first["revision"])
    assert second["revision"] > first["revision"] and second["changed"]
    with pytest.raises(ValueError, match="changed"):
        names._update(
            doc,
            doc.devices[0].device_id,
            NicknameUpdate(expected_revision=first["revision"], nickname="stale"),
        )
    assert second["names"] == first["names"]


def test_quarantine_limit_requires_manual_recovery_without_more_copies(tmp_path):
    store, doc, names = saved_names(tmp_path)
    for n in range(5):
        store._atomic_write(tmp_path / f"nicknames.corrupt-{n:032x}.json", "old corruption")
    store._atomic_write(names.path, "new corruption")
    with pytest.raises(ValueError, match="quarantine limit"):
        names._snapshot(doc, None)
    assert len(list(tmp_path.glob("nicknames.corrupt-*.json"))) == 5
    assert names.path.read_text() == "new corruption"
    assert not (tmp_path / "nicknames.recovery.json").exists()


@pytest.mark.parametrize(
    "unsafe_name", ["nicknames.json", "nicknames.previous.json", "nicknames.recovery.json"]
)
def test_symlink_paths_never_replaced_or_followed(tmp_path, monkeypatch, unsafe_name):
    from pathlib import Path

    store, doc, names = saved_names(tmp_path)
    store._atomic_write(names.path, "invalid primary")
    target = tmp_path / unsafe_name
    if not target.exists():
        store._atomic_write(target, '{"revision": 3}')
    before = target.read_bytes()
    is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == target or is_symlink(path))
    with pytest.raises(ValueError):
        names._snapshot(doc, None)
    assert target.read_bytes() == before


@pytest.mark.parametrize(
    "failure,status", [(OSError(errno.EIO, "read failure"), 503), (ValueError("bad JSON"), 409)]
)
def test_api_storage_errors_preserve_readable_report(monkeypatch, failure, status):
    manager = SessionManager()
    with TestClient(
        create_app(session_manager=manager), base_url=BASE_URL, raise_server_exceptions=False
    ) as client:
        doc = document()
        client.portal.call(client.app.state.store.create_scan, doc)
        headers = authenticate_client(client, manager)
        base = f"/api/live-scans/{doc.scan_id}"

        def fail(*args):
            raise failure

        monkeypatch.setattr(NicknameStore, "_load", fail)
        monkeypatch.setattr(NicknameStore, "_load_locked", fail)
        response = client.get(base + "/nicknames")
        assert response.status_code == status and "reload" in response.json()["detail"].lower()
        assert (
            client.put(
                base + f"/devices/{doc.devices[0].device_id}/nickname",
                headers=headers,
                json={"nickname": "TV", "expected_revision": 1},
            ).status_code
            == status
        )
        report = client.get(base)
        assert report.status_code == 200 and "nickname_error" in report.json()
        assert (
            client.put(
                base + f"/devices/{uuid4()}/nickname",
                headers=headers,
                json={"nickname": "TV", "expected_revision": 1},
            ).status_code
            == 404
        )


def test_api_disk_full_returns_readable_503_without_evidence_changes(monkeypatch):
    manager = SessionManager()
    with TestClient(
        create_app(session_manager=manager), base_url=BASE_URL, raise_server_exceptions=False
    ) as client:
        store = client.app.state.store
        doc = document()
        client.portal.call(store.create_scan, doc)
        headers = authenticate_client(client, manager)
        before = (store._scan_dir(doc.scan_id) / "scan.json").read_bytes()

        def fail(*args, **kwargs):
            raise OSError(errno.ENOSPC, "full disk")

        monkeypatch.setattr(store, "_atomic_write", fail)
        response = client.put(
            f"/api/live-scans/{doc.scan_id}/devices/{doc.devices[0].device_id}/nickname",
            headers=headers,
            json={"nickname": "TV", "expected_revision": 1},
        )
        assert response.status_code == 503 and "unchanged" in response.json()["detail"]
        assert (store._scan_dir(doc.scan_id) / "scan.json").read_bytes() == before
