"""At-most-one admission per explicit intention; no scanner/provider network work."""

import asyncio
import hashlib
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.jobs.start_requests import StartReceipt, StartRequests
from app.main import create_app
from app.schemas.api import ScanCreateRequest
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tests.fixtures.provider import ReviewedProvider
from tests.session_helpers import BASE_URL, authenticate_client


def intent(**changes):
    return ScanCreateRequest(
        **{
            "operation_id": uuid4(),
            "mode": "known_hosts",
            "hosts": ["192.168.56.10"],
            "profile": "light",
            "authorised": True,
            "confirmed_scope": "192.168.56.0/24",
            **changes,
        }
    )


def test_start_receipt_recovery_auth_conflict_connection_and_removed_report(monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda _: (True, "synthetic"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda _: "synthetic-nmap")
    monkeypatch.setattr("app.api.scans.mdns_available", lambda: False)
    manager, admitted = SessionManager(), []

    async def capture(scan_id):
        admitted.append(scan_id)

    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        client.app.state.explanations.provider = ReviewedProvider()
        monkeypatch.setattr(client.app.state.supervisor, "start", capture)
        body = intent().model_dump(mode="json")
        headers = authenticate_client(client, manager)
        path = f"/api/scan-starts/{body['operation_id']}"
        assert client.post("/api/live-scans", json=body).status_code == 403
        first = client.post("/api/live-scans", headers=headers, json=body)
        assert first.status_code == 202, first.text
        scan_id = first.json()["scan_id"]
        before = client.app.state.store._scan_dir(scan_id).joinpath("scan.json").read_bytes()
        second = client.post("/api/live-scans", headers=headers, json=body)
        assert second.status_code == 202 and second.json()["scan_id"] == scan_id
        assert admitted == [scan_id]
        assert client.get(path).json()["scan_id"] == scan_id
        changed = {**body, "hosts": ["192.168.56.11"]}
        assert client.post("/api/live-scans", headers=headers, json=changed).status_code == 409
        monkeypatch.setattr(
            "app.scanner.network.connection_snapshot", lambda *a, **k: {"different": True}
        )
        assert client.post("/api/live-scans", headers=headers, json=body).status_code == 409
        assert client.get(path).json()["scan_id"] == scan_id  # Historical reads remain available.
        assert (
            client.app.state.store._scan_dir(scan_id).joinpath("scan.json").read_bytes() == before
        )
        client.app.state.store._delete_scan(scan_id)  # Only this test's isolated report.
        assert client.get(path).json()["state"] == "report_unavailable"
        assert client.post("/api/live-scans", headers=headers, json=body).status_code == 409
        assert admitted == [scan_id]


@pytest.mark.asyncio
async def test_concurrent_tabs_and_disconnected_caller_share_owned_start(tmp_path):
    store = JsonStore(tmp_path)
    coordinator = StartRequests(store, SimpleNamespace(is_active=lambda _: True))
    body, entered, release, calls = intent(), asyncio.Event(), asyncio.Event(), []

    async def create(scan_id, operation):
        calls.append(scan_id)
        entered.set()
        await release.wait()
        await store.create_scan(
            ScanDocument(
                scan_id=scan_id, policy={"start_operation_id": operation}, target={"mode": "demo"}
            )
        )
        return {"scan_id": scan_id}

    async def valid(doc):
        assert doc is not None

    first = asyncio.create_task(coordinator.submit(body, create, valid))
    await entered.wait()
    second = asyncio.create_task(coordinator.submit(body, create, valid))
    status = await coordinator.status(str(body.operation_id))
    assert status["state"] == "preparing" and status["scan_id"] is None
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    release.set()
    result = await asyncio.wait_for(second, 3)
    assert calls == [result["scan_id"]]
    assert (await coordinator.status(str(body.operation_id)))["scan_id"] == result["scan_id"]
    # A new process recovers the durable receipt; it never calls create again.
    restarted = StartRequests(store, coordinator.supervisor)
    assert (await restarted.submit(body, create, valid))["scan_id"] == result["scan_id"]
    assert len(calls) == 1
    await restarted.shutdown()


@pytest.mark.asyncio
async def test_reserved_before_crash_and_corrupt_journal_never_reexecute(tmp_path):
    store = JsonStore(tmp_path)
    coordinator = StartRequests(store, SimpleNamespace(is_active=lambda _: False))
    body = intent()
    payload = body.model_dump(mode="json", exclude={"operation_id"})
    coordinator._transaction(
        str(body.operation_id),
        create=StartReceipt(
            scan_id=uuid4(),
            fingerprint=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            request=payload,
            created_at="2026-10-20T00:00:00Z",
            state="preparing",
        ),
    )

    async def forbidden(*args):
        pytest.fail("Recovery must not execute a new start")

    assert (await coordinator.status(str(body.operation_id)))["state"] == "interrupted"
    with pytest.raises(HTTPException) as failed:
        await coordinator.submit(body, forbidden, forbidden)
    assert failed.value.status_code == 409
    coordinator.path.write_text("invalid json")
    with pytest.raises(HTTPException) as failed:
        await coordinator.submit(body, forbidden, forbidden)
    assert failed.value.status_code == 503


@pytest.mark.asyncio
async def test_shutdown_finishes_unadmitted_saved_check_truthfully(tmp_path):
    store = JsonStore(tmp_path)
    coordinator = StartRequests(store, SimpleNamespace(is_active=lambda _: False))
    entered, body = asyncio.Event(), intent()

    async def create(scan_id, operation):
        await store.create_scan(
            ScanDocument(
                scan_id=scan_id,
                policy={"start_operation_id": operation},
                target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
                coverage={"targets": [{"ip": "192.168.56.10", "service_status": "pending"}]},
            )
        )
        entered.set()
        await asyncio.Event().wait()

    caller = asyncio.create_task(coordinator.submit(body, create, None))
    await entered.wait()
    await coordinator.shutdown()
    with pytest.raises(asyncio.CancelledError):
        await caller
    status = await coordinator.status(str(body.operation_id))
    doc = await store.load_scan(status["scan_id"])
    assert doc.state == "failed" and doc.phase == "finished"
    assert doc.unfinished_device_count == 1 and doc.coverage.service_completed_count == 0


def test_targeted_retry_receipt_only_rechecks_unfinished_device(monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda _: (True, "synthetic"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda _: "synthetic-nmap")
    monkeypatch.setattr("app.api.scans.mdns_available", lambda: False)
    manager, admitted = SessionManager(), []

    async def capture(scan_id):
        admitted.append(scan_id)

    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        client.app.state.explanations.provider = ReviewedProvider()
        monkeypatch.setattr(client.app.state.supervisor, "start", capture)
        original = ScanDocument(
            scan_id=str(uuid4()),
            phase="finished",
            state="partial",
            policy={"profile": "light", "allowed_network": "192.168.56.0/24"},
            target={"mode": "discover", "cidr": "192.168.56.0/24"},
            coverage={
                "targets": [
                    {
                        "ip": "192.168.56.10",
                        "service_status": "completed",
                        "discovery_status": "observed",
                    },
                    {
                        "ip": "192.168.56.11",
                        "service_status": "failed",
                        "discovery_status": "observed",
                    },
                ]
            },
        )
        client.app.state.store._create_scan(original)
        primary = client.app.state.store._scan_dir(original.scan_id) / "scan.json"
        before = primary.read_bytes()
        headers = authenticate_client(client, manager)
        operation = str(uuid4())
        body = {"operation_id": operation, "expected_revision": original.revision}
        url = f"/api/live-scans/{original.scan_id}/retry-hosts"
        first = client.post(url, headers=headers, json=body)
        assert first.status_code == 202, first.text
        scan_id = first.json()["scan_id"]
        assert client.post(url, headers=headers, json=body).json()["scan_id"] == scan_id
        retry = client.app.state.store._load_scan(scan_id)
        assert retry.target == {"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.11"]}
        assert retry.policy["retry_of"] == str(original.scan_id)
        assert client.get(f"/api/scan-starts/{operation}").json()["scan_id"] == scan_id
        # A different report cannot reuse the first retry intention, even with the same host.
        other = original.model_copy(update={"scan_id": str(uuid4())})
        client.app.state.store._create_scan(other)
        assert (
            client.post(
                f"/api/live-scans/{other.scan_id}/retry-hosts", headers=headers, json=body
            ).status_code
            == 409
        )
        assert admitted == [scan_id] and primary.read_bytes() == before


@pytest.mark.asyncio
async def test_rejected_preflight_is_not_reexecuted_and_full_journal_fails_closed(tmp_path):
    store = JsonStore(tmp_path)
    coordinator = StartRequests(store, SimpleNamespace(is_active=lambda _: False))
    body, calls = intent(), []

    async def rejected(*args):
        calls.append(args)
        raise HTTPException(503, "Synthetic unavailable scanner")

    with pytest.raises(HTTPException):
        await coordinator.submit(body, rejected, None)
    assert (await coordinator.status(str(body.operation_id)))["state"] == "rejected"
    with pytest.raises(HTTPException) as failed:
        await coordinator.submit(body, rejected, None)
    assert failed.value.status_code == 409 and len(calls) == 1
    record = coordinator._transaction(str(body.operation_id))
    operations = {str(uuid4()): record.model_dump(mode="json") for _ in range(1024)}
    coordinator.path.write_text(json.dumps({"operations": operations}))
    before = coordinator.path.read_bytes()
    with pytest.raises(HTTPException) as failed:
        await coordinator.submit(intent(), rejected, None)
    assert failed.value.status_code == 409 and len(calls) == 1
    assert coordinator.path.read_bytes() == before
