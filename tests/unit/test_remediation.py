from types import SimpleNamespace

import pytest
from app.scanner.cpe_identity import resolve_identity
from app.scanner.diagnostics import process_failure
from app.scanner.network import NetworkGuard, NetworkInterrupted
from app.scanner.runner import ProcessResult


@pytest.mark.asyncio
async def test_supervisor_stops_before_probe_when_context_changed(tmp_path, monkeypatch):
    from uuid import uuid4

    from app.jobs.supervisor import ScanSupervisor
    from app.schemas.scan import ScanDocument
    from app.storage.json_store import JsonStore

    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": ["192.168.0.2"]},
        policy={"allowed_network": "192.168.0.0/24", "network_context": {"adapter": 1}},
        coverage={"targets": [{"ip": "192.168.0.2", "service_status": "pending"}]},
    )
    await store.create_scan(doc)
    monkeypatch.setattr("app.scanner.network.connection_snapshot", lambda *a: {"adapter": 2})

    async def forbidden(*args):
        pytest.fail("Network changed; scanner must not run")

    supervisor = ScanSupervisor(store, process_runner=forbidden)
    await supervisor._run(doc.scan_id, __import__("asyncio").Event())
    saved = await store.load_scan(doc.scan_id)
    assert saved.state == "failed"
    assert saved.errors[0]["code"] == "NETWORK_INTERRUPTED"
    assert saved.coverage.targets[0].attempts == 0


@pytest.mark.asyncio
async def test_network_guard_rejects_changes_and_stays_failed():
    expected = {"adapter": 1, "gateway": "192.168.0.1"}
    observed = dict(expected)
    guard = NetworkGuard(expected, lambda: observed)
    await guard.check()
    observed["adapter"] = 2
    with pytest.raises(NetworkInterrupted):
        await guard.check()
    observed.update(expected)
    with pytest.raises(NetworkInterrupted):
        await guard.check()


@pytest.mark.asyncio
async def test_network_guard_rejects_suspend_without_probing():
    guard = NetworkGuard({}, lambda: pytest.fail("Do not resume probing after suspension"))
    guard.last_tick -= 60
    with pytest.raises(NetworkInterrupted):
        await guard.check()


def test_windows_structured_network_detection_is_locale_independent(monkeypatch):
    from app.config import detect_private_network

    monkeypatch.setattr("app.config.os", SimpleNamespace(name="nt"))
    rows = [
        {
            "Profile": "Heimnetz",
            "Gateways": ["192.168.0.1"],
            "Addresses": [{"IPAddress": "192.168.0.216", "PrefixLength": 24}],
        }
    ]
    monkeypatch.setattr("app.scanner.network.windows_connections", lambda: rows)
    assert detect_private_network() == "192.168.0.0/24"
    rows.append(
        {"Gateways": ["10.0.0.1"], "Addresses": [{"IPAddress": "10.0.0.2", "PrefixLength": 24}]}
    )
    assert detect_private_network() is None


@pytest.mark.parametrize(
    "stderr,code",
    [
        (b"requires root privileges", "HOST_PRIVILEGE_REQUIRED"),
        (b"failed to open device Npcap", "HOST_DRIVER_UNAVAILABLE"),
        (b"unknown error", "HOST_SCAN_FAILED"),
    ],
)
def test_scanner_failure_classification_does_not_reveal_stderr(stderr, code):
    assert process_failure(ProcessResult(b"", stderr, 1, 0.1)) == code


@pytest.mark.asyncio
async def test_dictionary_resolves_unique_product_version_with_provenance():
    old = "cpe:2.3:a:old_vendor:product:1.0:*:*:*:*:*:*:*"
    deprecated = old.replace("old_vendor", "previous_vendor")
    current = old.replace("old_vendor", "current_vendor")
    calls = []

    async def fetch(url, params):
        calls.append(params["cpeMatchString"])
        pattern = params["cpeMatchString"]
        rows = (
            []
            if pattern == old
            else [{"cpe": {"cpeName": current, "deprecated": False}}]
            if pattern == current
            else [
                {
                    "cpe": {
                        "cpeName": deprecated,
                        "deprecated": True,
                        "deprecatedBy": [{"cpeName": current}],
                    }
                }
            ]
        )
        return {"products": rows, "totalResults": len(rows)}

    resolved, method, evidence = await resolve_identity(old, fetch)
    assert resolved == current
    assert method == "unique_product_version_candidate"
    assert set(evidence) == {deprecated, current}
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_dictionary_does_not_choose_between_vendors():
    query = "cpe:2.3:a:original:product:1.0:*:*:*:*:*:*:*"

    async def fetch(url, params):
        rows = (
            []
            if params["cpeMatchString"] == query
            else [
                {"cpe": {"cpeName": query.replace("original", vendor), "deprecated": False}}
                for vendor in ("one", "two")
            ]
        )
        return {"products": rows, "totalResults": len(rows)}

    resolved, reason, _ = await resolve_identity(query, fetch)
    assert resolved is None and reason == "ambiguous"
