import asyncio
import errno
from uuid import uuid4

import pytest
from app.jobs.supervisor import ScanSupervisor
from app.main import create_app
from app.profiling.history import compare_history
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import AnnotationStore, TitleUpdate
from app.storage.json_store import JsonStore
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client
from tests.unit.test_action_checks import document, update
from tests.unit.test_device_details import document as history_document


@pytest.mark.parametrize("operation", ["read", "title", "checklist"])
def test_note_io_errors_are_readable_and_retry_preserves_evidence(monkeypatch, operation):
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        store = client.app.state.store
        doc = document()
        client.portal.call(store.create_scan, doc)
        notes = AnnotationStore(store)
        notes._update(doc.scan_id, title=TitleUpdate(title="Saved", expected_revision=1))
        folder = store._scan_dir(doc.scan_id)
        evidence = (folder / "scan.json").read_bytes()
        saved = (folder / "annotations.json").read_bytes()
        headers = authenticate_client(client, manager)
        url = f"/api/live-scans/{doc.scan_id}"

        def fail(*args, **kwargs):
            raise OSError(errno.ENOSPC, "private disk path must not leak")

        with monkeypatch.context() as patch:
            if operation == "read":
                original_read = store._read_json

                def unreadable(path):
                    if path.name.startswith("annotations"):
                        return fail()
                    return original_read(path)

                patch.setattr(store, "_read_json", unreadable)
                response = client.get(url + "/annotations")
            else:
                patch.setattr(store, "_atomic_write", fail)
                body = (
                    {"title": "New", "expected_revision": 2}
                    if operation == "title"
                    else update(doc, revision=2).model_dump()
                )
                response = client.put(
                    url + ("/title" if operation == "title" else "/action-checks"),
                    json=body,
                    headers=headers,
                )
            assert response.status_code == 503
            assert "Original scan results are preserved" in response.json()["detail"]
            assert "private disk" not in response.text
        assert (folder / "scan.json").read_bytes() == evidence
        assert (folder / "annotations.json").read_bytes() == saved
        assert client.get(url + "/annotations").status_code == 200
        assert (
            client.put(
                url + "/title", json={"title": "Retry", "expected_revision": 2}, headers=headers
            ).status_code
            == 200
        )
        assert (folder / "scan.json").read_bytes() == evidence


def test_corrupt_note_copies_are_not_reset_by_api():
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        store = client.app.state.store
        doc = document()
        client.portal.call(store.create_scan, doc)
        folder = store._scan_dir(doc.scan_id)
        evidence = (folder / "scan.json").read_bytes()
        for name in ("annotations.json", "annotations.previous.json"):
            store._atomic_write(folder / name, "broken")
        assert client.get(f"/api/live-scans/{doc.scan_id}/annotations").status_code == 401
        headers = authenticate_client(client, manager)
        for response in (
            client.get(f"/api/live-scans/{doc.scan_id}/annotations"),
            client.put(
                f"/api/live-scans/{doc.scan_id}/title",
                json={"title": "No reset", "expected_revision": 1},
                headers=headers,
            ),
        ):
            assert response.status_code == 409
            assert "reload before saving" in response.json()["detail"]
        assert (folder / "scan.json").read_bytes() == evidence
        assert (folder / "annotations.json").read_text() == "broken"
        assert (folder / "annotations.previous.json").read_text() == "broken"


def test_failed_atomic_note_replacement_keeps_primary_and_allows_retry(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    doc = document()
    store._create_scan(doc)
    notes = AnnotationStore(store)
    notes._update(doc.scan_id, title=TitleUpdate(title="Saved", expected_revision=1))
    folder = store._scan_dir(doc.scan_id)
    evidence = (folder / "scan.json").read_bytes()
    primary = (folder / "annotations.json").read_bytes()
    import app.storage.json_store as module

    original_replace = module.os.replace

    def fail_notes(source, target):
        if target.name == "annotations.json":
            raise OSError(errno.EIO, "synthetic atomic replace failure")
        return original_replace(source, target)

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "replace", fail_notes)
        with pytest.raises(OSError):
            notes._update(doc.scan_id, title=TitleUpdate(title="Uncommitted", expected_revision=2))
    assert (folder / "annotations.json").read_bytes() == primary
    assert (folder / "annotations.previous.json").read_bytes() == primary
    assert not list(folder.glob(".w-*.tmp"))
    assert (
        notes._update(doc.scan_id, title=TitleUpdate(title="Retry", expected_revision=2)).revision
        == 3
    )
    assert (folder / "scan.json").read_bytes() == evidence


@pytest.mark.parametrize("reason", ["profile", "ports", "incomplete"])
def test_history_discloses_specific_incompatible_reason(reason):
    current = history_document()
    previous = history_document(created="2026-09-24T22:00:00Z")
    current.devices[0].mac = previous.devices[0].mac = "aa:bb:cc:dd:ee:ff"
    if reason == "profile":
        current.policy["profile_id"] = "deep"
        expected = "different profiles"
    elif reason == "ports":
        current.policy.pop("tcp_ports")
        expected = "were not recorded"
    else:
        current.coverage.targets[0].service_status = "timed_out"
        expected = "did not finish"
    compare_history(current, [previous])
    detail = current.devices[0].details[-1]
    assert detail.status == "not_checked" and expected in detail.value
    assert "No conclusion" in detail.value


@pytest.mark.asyncio
async def test_five_ai_retries_bound_all_jobs_and_release_capacity(tmp_path):
    store = JsonStore(tmp_path)
    started, release = asyncio.Event(), asyncio.Event()

    class WaitingService:
        async def explain_scan(self, scan_id):
            started.set()
            await release.wait()

    supervisor = ScanSupervisor(store, explanation_service=WaitingService())
    docs = [
        ScanDocument(
            scan_id=str(uuid4()),
            state="completed",
            phase="finished",
            target={"mode": "known_hosts", "hosts": ["192.168.0.2"]},
        )
        for _ in range(6)
    ]
    for doc in docs:
        await store.create_scan(doc)
    untouched = (store._scan_dir(docs[-1].scan_id) / "scan.json").read_bytes()
    try:
        for doc in docs[:5]:
            await supervisor.request_explanations(doc.scan_id)
        await started.wait()
        assert supervisor.active_scan_count == 5 and not supervisor.has_capacity()
        with pytest.raises(RuntimeError, match="SCAN_CAPACITY"):
            await supervisor.request_explanations(docs[-1].scan_id)
        assert (store._scan_dir(docs[-1].scan_id) / "scan.json").read_bytes() == untouched
        with pytest.raises(RuntimeError, match="SCAN_CAPACITY"):
            await supervisor.start(docs[-1].scan_id)
        # Automatic AI and its awaiting scan share one admission.
        supervisor._tasks[docs[0].scan_id] = supervisor._analysis_tasks[docs[0].scan_id]
        assert supervisor.active_scan_count == 5
        supervisor._tasks.pop(docs[0].scan_id)
        await supervisor.cancel(docs[4].scan_id)
        assert supervisor.active_scan_count == 4 and supervisor.has_capacity()
        await supervisor.request_explanations(docs[5].scan_id)
        assert supervisor.active_scan_count == 5
        release.set()
        await asyncio.gather(*list(supervisor._analysis_tasks.values()))
        assert supervisor.active_scan_count == 0 and supervisor.has_capacity()
    finally:
        release.set()
        await supervisor.shutdown()


@pytest.mark.asyncio
async def test_ai_queue_expiry_releases_admission(tmp_path):
    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "hosts": ["192.168.0.2"]},
    )
    await store.create_scan(doc)
    supervisor = ScanSupervisor(store, explanation_service=object(), max_concurrent_scans=1)
    supervisor.queue_timeout_s = 0.01
    await supervisor._analysis_capacity.acquire()
    await supervisor.request_explanations(doc.scan_id)
    await asyncio.gather(*list(supervisor._analysis_tasks.values()))
    assert supervisor.has_capacity() and supervisor.active_scan_count == 0
    assert (await store.load_scan(doc.scan_id)).phase == "finished"
    supervisor._analysis_capacity.release()


def test_ai_capacity_api_is_inline_retryable_and_does_not_start_scan(monkeypatch):
    async def available(self):
        return True

    async def full(self, scan_id):
        raise RuntimeError("SCAN_CAPACITY")

    monkeypatch.setattr("app.explanations.service.ExplanationService.provider_available", available)
    monkeypatch.setattr(ScanSupervisor, "request_explanations", full)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        doc = document()
        client.portal.call(client.app.state.store.create_scan, doc)
        headers = authenticate_client(client, manager)
        response = client.post(
            f"/api/live-scans/{doc.scan_id}/explanations", json={}, headers=headers
        )
        assert response.status_code == 429 and response.headers["Retry-After"] == "10"
        assert "saved report is unchanged" in response.json()["detail"]
        assert not client.app.state.supervisor.active_scan_ids
