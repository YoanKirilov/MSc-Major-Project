"""Periodic submissions use the normal scan validator, never a second scanner."""

import asyncio
from types import SimpleNamespace

import pytest
from app.api.scans import _create_validated_live_scan
from app.config import load_config
from app.jobs.supervisor import ScanSupervisor
from app.schemas.api import ScanCreateRequest
from app.schemas.settings import SettingsUpdate
from app.storage.json_store import JsonStore
from fastapi import HTTPException


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["manual", "ai"])
async def test_periodic_admission_is_atomic_with_manual_and_ai_jobs(tmp_path, monkeypatch, source):
    supervisor = ScanSupervisor(JsonStore(tmp_path))
    release = asyncio.Event()

    async def wait_only(scan_id, cancel_event):
        await release.wait()

    monkeypatch.setattr(supervisor, "_run", wait_only)
    if source == "manual":
        await supervisor.start("manual")
    else:
        supervisor._analysis_tasks["ai"] = asyncio.create_task(release.wait())
    try:
        with pytest.raises(RuntimeError, match="SCAN_BUSY"):
            await supervisor.start("periodic", require_idle=True)
        assert "periodic" not in supervisor._tasks
    finally:
        release.set()
        await supervisor.shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["changed_connection", "busy_before", "busy_race", "idle"])
async def test_periodic_request_rechecks_context_and_never_leaves_a_rejected_scan(
    tmp_path, monkeypatch, case
):
    scope = "192.168.56.0/24"
    store = JsonStore(tmp_path)
    await store.update_settings(
        SettingsUpdate(expected_revision=1, allowed_network=scope, mdns_enabled=False), 1
    )
    context = {"address": "192.168.56.10", "interface": "test", "scope": scope}
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "synthetic"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "synthetic")
    monkeypatch.setattr("app.api.scans.detect_private_network", lambda: scope)
    monkeypatch.setattr("app.scanner.network.connection_snapshot", lambda *a, **kw: context)
    calls = []

    async def start(scan_id, **options):
        calls.append(options)
        if case == "busy_race":
            raise RuntimeError("SCAN_BUSY")

    async def available():
        return True

    supervisor = SimpleNamespace(
        nmap_path="", active_scan_count=int(case == "busy_before"), start=start
    )
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                config=load_config(),
                store=store,
                supervisor=supervisor,
                explanations=SimpleNamespace(provider_available=available),
            )
        )
    )
    body = ScanCreateRequest(
        mode="discover", cidr=scope, profile="light", authorised=True, confirmed_scope=scope
    )
    approved = {**context, "address": "192.168.56.11"} if case == "changed_connection" else context
    if case == "idle":
        reply = await _create_validated_live_scan(request, body, approved_context=approved)
        assert reply["state"] == "queued" and calls == [{"require_idle": True}]
        assert (await store.list_scans(source=None, offset=0, limit=20))["total"] == 1
    else:
        with pytest.raises(HTTPException) as result:
            await _create_validated_live_scan(request, body, approved_context=approved)
        assert result.value.status_code == (409 if case == "changed_connection" else 429)
        assert (await store.list_scans(source=None, offset=0, limit=20))["total"] == 0
