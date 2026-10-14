"""Synthetic periodic scheduling only: no scanners, providers or normal saved data."""

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.api.monitoring import router
from app.config import AppConfig
from app.jobs.monitoring import MonitoringService
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from app.storage.monitoring import (
    MAX_EVENTS,
    MAX_MONITOR_BYTES,
    MonitoringDocument,
    MonitoringRevisionConflict,
    MonitoringStore,
    MonitoringUnavailable,
    MonitoringUpdate,
    add_event,
)
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.session_helpers import BASE_URL

SCOPE = "192.168.56.0/24"
DATE = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


class Clock:
    value = 0.0

    def __call__(self):
        return self.value

    def wall(self):
        return DATE + timedelta(seconds=self.value)


@pytest.fixture
def fixture_app(tmp_path, monkeypatch):
    app = FastAPI()
    app.state.store = JsonStore(tmp_path)
    app.state.config = AppConfig(data_dir=tmp_path, allowed_network=SCOPE)
    app.state.supervisor = SimpleNamespace(active_scan_count=0)
    manager = SessionManager()
    app.state.session_manager = manager
    calls, snapshots = [], []
    context = {
        "address": "192.168.56.2",
        "interface": "synthetic-interface",
        "connection": {"Profile": "Synthetic network", "Gateways": ["192.168.56.1"]},
    }
    detected = {"scope": SCOPE}
    monkeypatch.setattr("app.jobs.monitoring.detect_private_network", lambda: detected["scope"])

    def capture(*args, **kwargs):
        snapshots.append((args, kwargs))
        return deepcopy(context)

    monkeypatch.setattr("app.jobs.monitoring.connection_snapshot", capture)
    clock = Clock()

    async def submit(body, approved_context):
        calls.append((body, approved_context))
        scan_id = str(uuid4())
        await app.state.store.create_scan(
            ScanDocument(
                scan_id=scan_id,
                target={"mode": "discover", "cidr": body.cidr, "hosts": []},
                policy={"profile": "light", "allowed_network": body.cidr},
            )
        )
        return {"scan_id": scan_id, "state": "queued"}

    service = MonitoringService(app, clock=clock, wall_clock=clock.wall, submit=submit)
    app.state.monitoring = service
    app.include_router(router)
    return SimpleNamespace(
        app=app,
        service=service,
        store=app.state.store,
        clock=clock,
        context=context,
        detected=detected,
        calls=calls,
        snapshots=snapshots,
        manager=manager,
    )


async def enable(fixture, interval=30):
    status = await fixture.service.status()
    return await fixture.service.configure(
        MonitoringUpdate(
            expected_revision=status["revision"],
            enabled=True,
            authorised=True,
            confirmed_scope=SCOPE,
            interval_minutes=interval,
        )
    )


async def advance(fixture, seconds):
    end = fixture.clock.value + seconds
    while fixture.clock.value < end:
        fixture.clock.value = min(end, fixture.clock.value + 30)
        await fixture.service.tick(now=fixture.clock.value)


def files(store):
    return {
        str(path.relative_to(store.data_root)): path.read_bytes()
        for path in store.data_root.rglob("*")
        if path.is_file()
    }


def test_default_store_is_read_only_and_explicit_saves_are_revisioned_with_atomic_backup(tmp_path):
    store = JsonStore(tmp_path)
    monitoring = MonitoringStore(store)
    assert monitoring._load().enabled is False
    assert files(store) == {}
    first = monitoring._replace(MonitoringDocument(interval_minutes=30), 1)
    assert first.revision == 2
    assert first.interval_minutes == 30
    assert not monitoring.backup.exists()
    primary = monitoring.path.read_bytes()
    second = monitoring._replace(first.model_copy(update={"interval_minutes": 60}), 2)
    assert second.revision == 3
    assert monitoring.backup.read_bytes() == primary
    before = files(store)
    with pytest.raises(MonitoringRevisionConflict):
        monitoring._replace(first, 2)
    assert files(store) == before


@pytest.mark.parametrize(
    "values",
    [
        {"enabled": "true"},
        {"enabled": 1},
        {"expected_revision": True},
        {"interval_minutes": 29},
        {"interval_minutes": 1441},
        {"interval_minutes": "30"},
        {"interval_minutes": 30.0},
        {"authorised": "true"},
        {"extra_setting": True},
    ],
)
def test_monitoring_update_rejects_coercion_and_out_of_range_settings(values):
    with pytest.raises(ValidationError):
        MonitoringUpdate(**({"expected_revision": 1, "enabled": False, **values}))


@pytest.mark.parametrize("scope", ["8.8.8.0/24", "192.168.56.1/24", "192.168.0.0/16", "::1/128"])
def test_saved_monitoring_scope_is_a_bounded_canonical_private_ipv4_range(scope):
    with pytest.raises(ValidationError):
        MonitoringDocument(scope=scope)


def test_event_timeline_is_bounded_and_adjacent_repeated_conditions_are_quiet():
    document = MonitoringDocument()
    for index in range(130):
        document = add_event(document, "deferred", f"Synthetic condition {index}")
    assert len(document.events) == MAX_EVENTS
    assert document.events[0].message == "Synthetic condition 30"
    before = document.model_dump()
    assert add_event(document, "deferred", "Synthetic condition 129").model_dump() == before


def test_unreadable_or_missing_primary_never_resets_or_overwrites_existing_settings(tmp_path):
    store = JsonStore(tmp_path)
    monitoring = MonitoringStore(store)
    first = monitoring._replace(MonitoringDocument(), 1)
    monitoring._replace(first, first.revision)
    store._atomic_write(monitoring.path, "{corrupt")
    before = files(store)
    with pytest.raises(MonitoringUnavailable):
        monitoring._load()
    with pytest.raises(MonitoringUnavailable):
        monitoring._replace(MonitoringDocument(), 1)
    assert files(store) == before
    monitoring.path.unlink()
    with pytest.raises(MonitoringUnavailable):
        monitoring._load()
    assert monitoring.backup.exists()


def test_oversized_and_nonregular_paths_fail_closed(tmp_path):
    store = JsonStore(tmp_path)
    monitoring = MonitoringStore(store)
    store._atomic_write(monitoring.path, "x" * (MAX_MONITOR_BYTES + 1))
    before = monitoring.path.read_bytes()
    with pytest.raises(MonitoringUnavailable):
        monitoring._load()
    assert monitoring.path.read_bytes() == before
    monitoring.path.unlink()
    monitoring.path.mkdir()
    with pytest.raises(MonitoringUnavailable):
        monitoring._replace(MonitoringDocument(), 1)


def test_monitoring_symlinks_are_rejected_without_modifying_the_target(tmp_path):
    store = JsonStore(tmp_path)
    monitoring = MonitoringStore(store)
    target = tmp_path / "synthetic-target.json"
    store._atomic_write(target, MonitoringDocument().model_dump_json())
    try:
        monitoring.path.symlink_to(target)
    except OSError:
        pytest.skip("This Windows test user cannot create symlinks")
    before = target.read_bytes()
    with pytest.raises(MonitoringUnavailable):
        monitoring._load()
    with pytest.raises(MonitoringUnavailable):
        monitoring._replace(MonitoringDocument(), 1)
    assert target.read_bytes() == before


@pytest.mark.asyncio
async def test_default_service_start_close_and_status_create_no_monitoring_files(fixture_app):
    f = fixture_app
    before = files(f.store)
    await f.service.start()
    status = await f.service.status()
    assert status["revision"] == 1 and status["enabled"] is False
    assert status["current_scope"] == SCOPE and status["available"] is True
    assert status["next_check_at"] is None
    assert f.snapshots == [] and f.calls == []
    await f.service.close()
    assert files(f.store) == before
    assert f.service._task is None


@pytest.mark.asyncio
async def test_saved_enabled_schedule_is_paused_on_restart_without_any_write_or_submission(
    fixture_app,
):
    f = fixture_app
    saved = MonitoringDocument(
        enabled=True, scope=SCOPE, interval_minutes=30, next_check_at="2026-10-14T10:30:00Z"
    )
    f.service.store._replace(saved, 1)
    before = files(f.store)
    await f.service.start()
    status = await f.service.status()
    assert status["enabled"] is False
    assert status["pause_reason"] == "restarted" and status["next_check_at"] is None
    assert status["events"][-1]["kind"] == "paused"
    f.clock.value = 100_000
    await f.service.tick()
    await f.service.close()
    assert f.calls == [] and files(f.store) == before
    assert f.service.store._load().enabled is True


@pytest.mark.asyncio
async def test_restart_does_not_rewrite_old_queued_outcome_before_new_opt_in(fixture_app):
    f = fixture_app
    scan_id = str(uuid4())
    await f.store.create_scan(
        ScanDocument(
            scan_id=scan_id,
            state="cancelled",
            phase="finished",
            target={"mode": "discover", "cidr": SCOPE, "hosts": []},
        )
    )
    f.service.store._replace(
        MonitoringDocument(
            enabled=True,
            scope=SCOPE,
            next_check_at="2026-10-14T10:30:00Z",
            last_scan_id=scan_id,
            last_outcome="queued",
        ),
        1,
    )
    before = files(f.store)
    await f.service.tick(now=999_999)
    assert files(f.store) == before
    assert (await f.service.status())["enabled"] is False


@pytest.mark.asyncio
async def test_enabling_requires_explicit_permission_scope_and_current_exact_snapshot(fixture_app):
    f = fixture_app
    for kwargs in [
        {},
        {"authorised": True},
        {"authorised": True, "confirmed_scope": "192.168.57.0/24"},
    ]:
        with pytest.raises(HTTPException) as caught:
            await f.service.configure(MonitoringUpdate(expected_revision=1, enabled=True, **kwargs))
        assert caught.value.status_code in {409, 422}
    assert not f.service.store.path.exists()
    status = await enable(f)
    assert status["enabled"] is True and status["revision"] == 2
    assert len(f.snapshots) == 1 and f.snapshots[0][1]["strict"] is True
    assert status["next_check_at"] == "2026-10-14T10:30:00Z"
    assert f.calls == []
    encoded = f.service.store.path.read_text(encoding="utf-8")
    assert "Synthetic network" not in encoded and "approved_context" not in encoded


@pytest.mark.asyncio
async def test_light_submission_uses_shared_admission_only_after_the_interval(fixture_app):
    f = fixture_app
    await enable(f)
    await advance(f, 1799)
    assert f.calls == []
    await advance(f, 1)
    assert len(f.calls) == 1
    body, approved = f.calls[0]
    assert body.mode == "discover" and body.profile == "light" and body.hosts == []
    assert body.authorised is True and body.confirmed_scope == body.cidr == SCOPE
    assert approved == f.context
    status = await f.service.status()
    assert status["last_outcome"] == "queued"
    assert status["events"][-1]["kind"] == "started"
    assert status["next_check_at"] == "2026-10-14T11:00:00Z"


@pytest.mark.asyncio
async def test_sleep_reschedules_without_catch_up_or_burst(fixture_app):
    f = fixture_app
    await enable(f)
    f.clock.value = 10_000
    await f.service.tick()
    status = await f.service.status()
    assert f.calls == []
    assert "will not be replayed" in status["events"][-1]["message"]
    assert status["enabled"] is True
    await advance(f, 1799)
    assert f.calls == []
    await advance(f, 1)
    assert len(f.calls) == 1


@pytest.mark.asyncio
async def test_busy_scan_or_ai_work_skips_an_interval_without_snapshot_or_overlap(fixture_app):
    f = fixture_app
    await enable(f)
    f.app.state.supervisor.active_scan_count = 1
    await advance(f, 1800)
    assert f.calls == [] and len(f.snapshots) == 1
    status = await f.service.status()
    assert "scan or report explanation" in status["events"][-1]["message"]
    assert status["enabled"] is True
    f.app.state.supervisor.active_scan_count = 0
    await advance(f, 1800)
    assert len(f.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["snapshot", "scope", "missing"])
async def test_network_change_or_unavailable_connection_pauses_with_a_local_event(
    fixture_app, change
):
    f = fixture_app
    await enable(f)
    if change == "snapshot":
        f.context["connection"]["Gateways"] = ["192.168.56.254"]
    elif change == "scope":
        f.app.state.config.allowed_network = "192.168.57.0/24"
    else:
        f.detected["scope"] = None
    await advance(f, 1800)
    status = await f.service.status()
    assert f.calls == [] and status["enabled"] is False
    assert status["pause_reason"] == (
        "network_unavailable" if change == "missing" else "network_changed"
    )
    assert status["next_check_at"] is None and status["events"][-1]["kind"] == "paused"
    await advance(f, 3600)
    assert f.calls == []


@pytest.mark.asyncio
async def test_scope_status_is_cached_and_stop_works_when_current_scope_cannot_be_read(
    fixture_app, monkeypatch
):
    f = fixture_app
    reads = []
    monkeypatch.setattr(
        "app.jobs.monitoring.detect_private_network", lambda: reads.append(1) or SCOPE
    )
    await f.service.status()
    await f.service.status()
    assert len(reads) == 1 and f.snapshots == []
    await enable(f)
    f.app.state.config.allowed_network = None
    monkeypatch.setattr("app.jobs.monitoring.detect_private_network", lambda: None)
    f.clock.value = 61
    status = await f.service.status()
    assert status["current_scope"] is None and status["available"] is True
    stopped = await f.service.configure(
        MonitoringUpdate(
            expected_revision=status["revision"],
            enabled=False,
            authorised=False,
            confirmed_scope=None,
            interval_minutes=30,
        )
    )
    assert stopped["enabled"] is False and stopped["next_check_at"] is None


@pytest.mark.asyncio
async def test_outcomes_record_counts_and_conservative_comparisons_once(fixture_app):
    f = fixture_app
    await enable(f)
    await advance(f, 1800)
    scan_id = (await f.service.status())["last_scan_id"]
    device_id = str(uuid4())

    def finished(current):
        return ScanDocument.model_validate(
            {
                **current.model_dump(),
                "state": "partial",
                "phase": "finished",
                "coverage": {
                    "candidate_count": 2,
                    "discovered_count": 2,
                    "service_completed_count": 1,
                    "service_failed_count": 1,
                },
                "devices": [
                    {
                        "device_id": device_id,
                        "scan_id": scan_id,
                        "ip": "192.168.56.10",
                        "comparison": {
                            "status": "available",
                            "current_created_at": "2026-10-14T10:30:00Z",
                            "added_count": 1,
                        },
                    }
                ],
            }
        )

    await f.store.update_scan(scan_id, finished)
    await f.service.tick()
    status = await f.service.status()
    assert status["last_outcome"] == "partial"
    event = status["events"][-1]
    assert event["kind"] == "result"
    assert event["counts"]["completed_count"] == 1 and event["counts"]["unfinished_count"] == 1
    assert (
        event["counts"]["comparable_device_count"] == event["counts"]["changed_device_count"] == 1
    )
    assert "do not establish removal or a verified fix" in event["message"]
    before = f.service.store.path.read_bytes()
    await f.service.tick()
    assert f.service.store.path.read_bytes() == before


@pytest.mark.asyncio
async def test_default_submit_reuses_shared_guard_without_any_credentials(fixture_app, monkeypatch):
    f = fixture_app
    captures = []

    async def admission(request, body, *, approved_context):
        captures.append((request.app, body, approved_context))
        return {"scan_id": str(uuid4()), "state": "queued"}

    monkeypatch.setattr("app.api.scans._create_validated_live_scan", admission)
    f.service.submit = f.service._submit
    await enable(f)
    await advance(f, 1800)
    assert len(captures) == 1 and captures[0][0] is f.app
    assert captures[0][1].profile == "light" and captures[0][2] == f.context


@pytest.mark.asyncio
async def test_submission_timeout_pauses_without_cancelling_an_independent_handed_job(
    fixture_app, monkeypatch
):
    f = fixture_app
    job_started = asyncio.Event()
    job = asyncio.create_task(job_started.wait())

    async def stall(body, context):
        f.app.state.supervisor.active_scan_count = 1
        await asyncio.Event().wait()

    f.service.submit = stall
    monkeypatch.setattr("app.jobs.monitoring.SUBMISSION_TIMEOUT", 0.02)
    await enable(f)
    await advance(f, 1800)
    status = await f.service.status()
    assert status["enabled"] is False and status["pause_reason"] == "submission_failed"
    assert "time limit" in status["events"][-1]["message"]
    assert not job.done() and not job.cancelled()
    await advance(f, 3600)
    assert not job.done()
    job_started.set()
    await job


@pytest.mark.asyncio
async def test_close_is_bounded_when_submission_stalls_and_never_cancels_supervisor_jobs(
    fixture_app, monkeypatch
):
    f = fixture_app
    entered = asyncio.Event()
    independent_done = asyncio.Event()
    independent_job = asyncio.create_task(independent_done.wait())

    async def stall(body, context):
        entered.set()
        await asyncio.Event().wait()

    f.service.submit = stall
    monkeypatch.setattr("app.jobs.monitoring.SHUTDOWN_TIMEOUT", 0.02)
    await enable(f)
    await advance(f, 1799)
    f.clock.value = 1800
    f.service._task = asyncio.create_task(f.service.tick())
    await asyncio.wait_for(entered.wait(), timeout=1)
    await asyncio.wait_for(f.service.close(), timeout=1)
    assert f.service._task is None and not independent_job.done()
    independent_done.set()
    await independent_job


def test_authenticated_api_requires_csrf_strict_payloads_and_revisioned_changes(fixture_app):
    f = fixture_app
    with TestClient(f.app, base_url=BASE_URL) as client:
        assert client.get("/api/monitoring").status_code == 401
        session = f.manager.register_session()
        client.cookies.set("session_id", session)
        status = client.get("/api/monitoring").json()
        body = {
            "expected_revision": status["revision"],
            "enabled": True,
            "authorised": True,
            "confirmed_scope": SCOPE,
            "interval_minutes": 30,
        }
        assert (
            client.put("/api/monitoring", json=body, headers={"Origin": BASE_URL}).status_code
            == 403
        )
        headers = {"Origin": BASE_URL, "X-CSRF-Token": f.manager.csrf_for_session(session)}
        response = client.put("/api/monitoring", json=body, headers=headers)
        assert response.status_code == 200 and response.json()["enabled"] is True
        assert client.put("/api/monitoring", json=body, headers=headers).status_code == 409
        assert (
            client.put(
                "/api/monitoring", json={**body, "enabled": "true"}, headers=headers
            ).status_code
            == 422
        )
        assert (
            client.get("/api/monitoring", headers={"Host": "untrusted.example"}).status_code == 403
        )
        assert f.calls == []


@pytest.mark.asyncio
async def test_unreadable_monitoring_blocks_opt_in_and_failed_save_preserves_settings(
    fixture_app, monkeypatch
):
    f = fixture_app
    f.store._atomic_write(f.service.store.path, "{corrupt")
    original = f.service.store.path.read_bytes()
    status = await f.service.status()
    assert status["revision"] is None and status["available"] is False and not status["enabled"]
    with pytest.raises(HTTPException) as caught:
        await f.service.configure(MonitoringUpdate(expected_revision=1, enabled=False))
    assert caught.value.status_code == 503 and f.service.store.path.read_bytes() == original
    f.store._atomic_write(f.service.store.path, MonitoringDocument().model_dump_json())
    status = await f.service.status()
    assert status["revision"] == 1 and status["enabled"] is False
    await enable(f)
    before = f.service.store.path.read_bytes()

    def fail(*args):
        raise PermissionError("Synthetic denied write")

    monkeypatch.setattr(f.store, "_atomic_write", fail)
    with pytest.raises(HTTPException) as caught:
        await f.service.configure(MonitoringUpdate(expected_revision=2, enabled=False))
    assert caught.value.status_code == 503
    assert f.service.store.path.read_bytes() == before
    assert f.service._state.enabled is False and f.service._next_due is None
