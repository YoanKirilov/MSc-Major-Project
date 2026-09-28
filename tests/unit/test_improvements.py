import asyncio
from uuid import uuid4

import pytest
from app.explanations.presentation import plain_finding, plain_report
from app.explanations.service import ExplanationService
from app.explanations.wording import wording_choices
from app.jobs.supervisor import ScanSupervisor
from app.main import create_app
from app.scanner.parser import HostUnreachable, parse_host
from app.scanner.runner import ProcessResult
from app.schemas.scan import ScanDocument
from app.schemas.settings import SettingsUpdate
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from fastapi.testclient import TestClient
from filelock import FileLock, Timeout
from tests.fixtures.provider import ReviewedProvider
from tests.session_helpers import BASE_URL, authenticate_client
from tests.unit.test_explanations import make_stored_scan

DOWN_XML = (
    b'<nmaprun><runstats><finished exit="success"/>'
    b'<hosts up="0" down="1" total="1"/></runstats></nmaprun>'
)


def test_explicit_zero_hosts_is_unreachable_not_invalid_data():
    with pytest.raises(HostUnreachable):
        parse_host(DOWN_XML, "192.168.56.10", str(uuid4()))


@pytest.mark.parametrize(
    "xml",
    [
        b"<nmaprun>",
        DOWN_XML.replace(b'up="0"', b'up="1"'),
        DOWN_XML.replace(b'total="1"', b'total="2"'),
        DOWN_XML.replace(b'exit="success"', b'exit="error"'),
        b'<nmaprun><runstats><finished exit="success"/></runstats></nmaprun>',
    ],
)
def test_missing_or_contradictory_records_still_count_as_invalid(xml):
    with pytest.raises(ValueError) as error:
        parse_host(xml, "192.168.56.10", str(uuid4()))
    assert not isinstance(error.value, HostUnreachable)


@pytest.mark.parametrize("profile", ["light", "deep-tcp-v1"])
@pytest.mark.asyncio
async def test_unreachable_host_retries_without_inventing_completed_checks(tmp_path, profile):
    store = JsonStore(tmp_path)
    scan = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
        policy={"profile": profile},
        coverage={"candidate_count": 1, "targets": [{"ip": "192.168.56.10"}]},
    )
    await store.create_scan(scan)
    calls = []

    async def runner(*args):
        calls.append(args)
        return ProcessResult(DOWN_XML, b"", 0, 0.01)

    await ScanSupervisor(store, process_runner=runner)._run(scan.scan_id, asyncio.Event())
    result = await store.load_scan(scan.scan_id)
    assert len(calls) == 2
    assert result.state == "failed" and result.phase == "finished"
    assert result.coverage.service_failed_count == 1
    assert result.coverage.service_completed_count == 0
    assert result.coverage.targets[0].reason_code == "host_unreachable"
    assert result.errors[0]["code"] == "HOST_UNREACHABLE"
    assert not result.devices and not result.findings


def test_settings_and_report_locks_are_bounded_and_keep_existing_data(tmp_path, monkeypatch):
    monkeypatch.setattr(JsonStore, "lock_timeout_s", 0.05)
    store = JsonStore(tmp_path)
    scan = ScanDocument(scan_id=str(uuid4()), target={"mode": "demo"})
    store._create_scan(scan)
    before = (tmp_path / "scans" / scan.scan_id / "scan.json").read_bytes()
    with FileLock(str(tmp_path / "locks" / f"{scan.scan_id}.lock")):
        with pytest.raises(Timeout):
            store._update_scan(scan.scan_id, lambda current: current, None)
        assert store._load_scan(scan.scan_id).revision == scan.revision
    assert (tmp_path / "scans" / scan.scan_id / "scan.json").read_bytes() == before
    with FileLock(str(tmp_path / "settings.lock")):
        with pytest.raises(Timeout):
            store._update_settings(SettingsUpdate(expected_revision=1, mdns_enabled=True), 1)
    assert not (tmp_path / "settings.json").exists()


def test_busy_settings_api_returns_recoverable_error(monkeypatch):
    monkeypatch.setattr(JsonStore, "lock_timeout_s", 0.05)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        with FileLock(str(client.app.state.store.data_root / "settings.lock")):
            response = client.patch("/api/settings", json={"expected_revision": 1}, headers=headers)
        assert response.status_code == 503
        assert "busy" in response.json()["detail"]
        assert response.headers["retry-after"] == "1"


@pytest.mark.asyncio
async def test_plain_presentation_keeps_facts_and_originals_unchanged(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    before = document.model_dump()
    for finding in document.findings:
        plain = plain_finding(finding)
        assert plain["title"] == wording_choices(finding.title)[-1]
        assert plain["content"]["meaning"] == wording_choices(finding.fixed_explanation.meaning)[-1]
    assert "feature" in plain_report(document)["content"]["meaning"]
    assert before == document.model_dump()
    assert (await store.load_scan(document.scan_id)).devices == document.devices


@pytest.mark.asyncio
async def test_analysis_progress_is_saved_before_provider_and_survives_reload(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    observed = []

    class Provider(ReviewedProvider):
        async def generate(self, payload):
            # A new store stands in for a refreshed page reading the persisted checkpoint.
            progress = await JsonStore(tmp_path).load_progress(document.scan_id)
            observed.append(progress["analysis_progress"])
            return await super().generate(payload)

    result = await ExplanationService(store, Provider()).explain_scan(document.scan_id)
    total = len(document.findings) + 1
    assert observed[0] == {
        "state": "preparing",
        "total": total,
        "completed": 0,
        "active": total,
        "attempt": 1,
    }
    assert result.analysis_progress.completed == total
    assert result.analysis_progress.active == 0
    assert result.analysis_progress.state == "finished"
    assert result.findings == document.findings


@pytest.mark.asyncio
async def test_failed_ai_does_not_count_fallback_as_prepared(tmp_path):
    store, document = await make_stored_scan(tmp_path)

    class Provider(ReviewedProvider):
        async def generate(self, payload):
            raise ValueError("invalid output")

    result = await ExplanationService(store, Provider()).explain_scan(document.scan_id)
    assert result.analysis_status == "failed"
    assert result.analysis_progress.completed == 0
    assert result.analysis_progress.active == 0


@pytest.mark.asyncio
async def test_transient_storage_contention_is_not_a_scan_timeout(tmp_path, monkeypatch):
    store = JsonStore(tmp_path)
    document = ScanDocument(scan_id=str(uuid4()), target={"mode": "demo"})
    await store.create_scan(document)
    supervisor = ScanSupervisor(store)

    async def busy_checkpoint(*args):
        raise Timeout("synthetic-report.lock")

    monkeypatch.setattr(supervisor, "_checkpoint", busy_checkpoint)
    await supervisor._run(document.scan_id, asyncio.Event())
    result = await store.load_scan(document.scan_id)
    assert result.state == "failed"
    assert result.errors[0]["code"] == "STORAGE_BUSY"
    assert "storage was busy" in result.errors[0]["message"]


@pytest.mark.asyncio
async def test_analysis_progress_across_batches_and_cached_retry(tmp_path):
    store, document = await make_stored_scan(tmp_path)
    findings = [
        document.findings[0].model_copy(update={"finding_id": str(uuid4())}, deep=True)
        for _ in range(8)
    ]
    await store.update_scan(
        document.scan_id, lambda current: current.model_copy(update={"findings": findings})
    )
    observed = []

    class Provider(ReviewedProvider):
        async def generate(self, payload):
            saved = await JsonStore(tmp_path).load_progress(document.scan_id)
            observed.append(saved["analysis_progress"])
            return await super().generate(payload)

    service = ExplanationService(store, Provider())
    result = await service.explain_scan(document.scan_id)
    assert [(p["completed"], p["active"]) for p in observed] == [(0, 6), (6, 3)]
    assert result.analysis_progress.completed == result.analysis_progress.total == 9
    await service.explain_scan(document.scan_id)
    assert len(observed) == 2  # Matching saved wording is reused without new provider calls.


@pytest.mark.asyncio
async def test_report_api_adds_plain_presentation_without_rewriting_evidence():
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        authenticate_client(client, manager)
        store, document = await make_stored_scan(client.app.state.store.data_root)
        report = store.data_root / "scans" / document.scan_id / "scan.json"
        before = report.read_bytes()
        response = client.get(f"/api/live-scans/{document.scan_id}")
        assert response.status_code == 200
        payload = response.json()
        finding = document.findings[0]
        assert payload["plain_guidance"][finding.finding_id] == plain_finding(finding)
        assert payload["plain_overview"] == plain_report(document)
        assert payload["findings"][0]["title"] == finding.title
        assert "plain_guidance" not in document.model_dump()
        assert report.read_bytes() == before
