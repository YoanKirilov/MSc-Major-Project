from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from app.main import create_app
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import ActionCheckUpdate, AnnotationStore, TitleUpdate
from app.storage.json_store import JsonStore
from fastapi.testclient import TestClient
from tests.fixtures.fixtures import make_telnet_scan
from tests.session_helpers import BASE_URL, authenticate_client


def document():
    fixture = make_telnet_scan()
    return ScanDocument(
        scan_id=fixture["device"]["scan_id"],
        phase="finished",
        state="completed",
        target={"mode": "known_hosts", "hosts": ["192.168.0.10"]},
        devices=[fixture["device"]],
        services=[fixture["service"]],
        findings=[fixture["finding"]],
    )


def update(doc, status="checked", revision=1):
    return ActionCheckUpdate(
        finding_id=doc.findings[0].finding_id,
        action_id=doc.findings[0].actions[0].action_id,
        status=status,
        expected_revision=revision,
    )


def test_checklist_persists_merges_and_resets_without_changing_scan(tmp_path):
    store = JsonStore(tmp_path)
    doc = document()
    store._create_scan(doc)
    original = (store._scan_dir(doc.scan_id) / "scan.json").read_bytes()
    notes = AnnotationStore(store)
    notes._update(doc.scan_id, title=TitleUpdate(title="Review after update", expected_revision=1))
    checked = notes._update(doc.scan_id, action_check=update(doc, revision=2))
    assert checked.revision == 3 and checked.title == "Review after update"
    reloaded = AnnotationStore(JsonStore(tmp_path))._load(doc.scan_id)
    assert reloaded.action_checks[0].status == "checked"
    assert reloaded.action_checks[0].updated_at
    with pytest.raises(ValueError, match="changed"):
        notes._update(doc.scan_id, action_check=update(doc, "need_help", 2))
    needs_help = notes._update(doc.scan_id, action_check=update(doc, "need_help", 3))
    assert len(needs_help.action_checks) == 1
    assert needs_help.action_checks[0].status == "need_help"
    reset = notes._update(doc.scan_id, action_check=update(doc, "to_check", 4))
    assert reset.action_checks == [] and reset.title == checked.title
    assert (store._scan_dir(doc.scan_id) / "scan.json").read_bytes() == original


@pytest.mark.parametrize("invalid", ["finding", "action", "unfinished"])
def test_checklist_rejects_unsaved_actions_and_unfinished_reports(tmp_path, invalid):
    store = JsonStore(tmp_path)
    doc = document()
    if invalid == "unfinished":
        doc.phase, doc.state = "service_scan", "running"
    store._create_scan(doc)
    body = update(doc)
    if invalid == "finding":
        body.finding_id = "not-in-report"
    if invalid == "action":
        body.action_id = "not-in-finding"
    with pytest.raises(ValueError):
        AnnotationStore(store)._update(doc.scan_id, action_check=body)
    assert not (store._scan_dir(doc.scan_id) / "annotations.json").exists()


def test_concurrent_checklist_edits_reject_one_stale_revision(tmp_path):
    store = JsonStore(tmp_path)
    doc = document()
    store._create_scan(doc)
    barrier = Barrier(2)

    def save(status):
        barrier.wait(timeout=5)
        try:
            AnnotationStore(store)._update(doc.scan_id, action_check=update(doc, status))
            return "saved"
        except ValueError:
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, ["checked", "need_help"]))
    assert sorted(results) == ["saved", "stale"]
    assert AnnotationStore(store)._load(doc.scan_id).revision == 2


def test_action_check_api_requires_session_csrf_and_saved_action():
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        doc = document()
        client.portal.call(client.app.state.store.create_scan, doc)
        url = f"/api/live-scans/{doc.scan_id}/action-checks"
        body = update(doc).model_dump()
        assert client.put(url, json=body, headers={"Origin": BASE_URL}).status_code == 403
        headers = authenticate_client(client, manager)
        assert client.put(url, json=body).status_code == 403
        assert client.put(url, json={**body, "status": "safe"}, headers=headers).status_code == 422
        assert (
            client.put(url, json={**body, "action_id": "unknown"}, headers=headers).status_code
            == 409
        )
        assert client.put(url, json=body, headers=headers).status_code == 200
        assert client.put(url, json=body, headers=headers).status_code == 409
        saved = client.get(f"/api/live-scans/{doc.scan_id}/annotations").json()
        assert saved["action_checks"][0]["status"] == "checked"
        assert saved["revision"] == 2
