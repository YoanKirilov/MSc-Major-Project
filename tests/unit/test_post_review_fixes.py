"""Regression boundaries for the post-improvement audit; no network scans."""

import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import httpx
import pytest
from app.build_info import API_CONTRACT_VERSION, source_build_id
from app.jobs.transitions import close_unfinished
from app.main import create_app
from app.scanner.cve import NvdClient, product_applicability
from app.scanner.reverse_dns import ReverseDnsResolver
from app.scanner.runner import ProcessResult, run_process
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client
from tests.unit.test_cve_related import PRODUCT
from tests.unit.test_cves import CveProvider, nvd_data, software


@pytest.mark.asyncio
async def test_rich_history_mixed_load_is_isolated_and_preserves_evidence(tmp_path):
    from scripts.benchmark_library import benchmark

    rows = await benchmark(tmp_path, counts=(2,), rich=True)
    row = rows[0]
    assert row["source_files_preserved"]
    assert row["devices_per_report"] == 16 and row["services_per_report"] == 128
    assert row["cold"]["full_json_reads"] == 2
    assert row["warm"]["full_json_reads"] == 0
    mixed = row["mixed_load"]
    assert mixed["search_total"] == 3 and mixed["inventory_total"] == 16
    assert mixed["checkpoint_writes"] >= 3
    assert mixed["terminal_cancel_saved"] and mixed["capacity_released"]
    assert mixed["not_a_live_scanner_cancellation_measurement"]


def test_queue_expired_retry_uses_shared_eligibility_and_preserves_report(monkeypatch):
    import app.api.scans as routes

    calls = []

    async def capture(request, body, retry_of=None):
        calls.append((body, retry_of))
        return {"scan_id": str(uuid4())}

    monkeypatch.setattr(routes, "_create_validated_live_scan", capture)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        document = ScanDocument(
            scan_id=str(uuid4()),
            state="running",
            policy={"profile": "light"},
            target={"mode": "discover", "cidr": "192.168.56.0/24"},
            coverage={
                "discovered_count": 2,
                "candidate_count": 254,
                "targets": [
                    {
                        "ip": "192.168.56.10",
                        "discovery_status": "observed",
                        "service_status": "completed",
                    },
                    {
                        "ip": "192.168.56.11",
                        "discovery_status": "observed",
                        "service_status": "pending",
                    },
                    {
                        "ip": "192.168.56.12",
                        "discovery_status": "observed",
                        "service_status": "skipped",
                        "reason_code": "deliberately_excluded",
                    },
                    {
                        "ip": "192.168.56.13",
                        "discovery_status": "not_seen",
                        "service_status": "skipped",
                        "reason_code": "scan_queue_expired",
                    },
                ],
            },
        )
        document = close_unfinished(document, "scan_queue_expired").model_copy(
            update={"state": "partial", "phase": "finished"}
        )
        client.app.state.store._create_scan(document)
        primary = client.app.state.store._scan_dir(document.scan_id) / "scan.json"
        before = primary.read_bytes()
        headers = authenticate_client(client, manager)
        assert client.get(f"/api/live-scans/{document.scan_id}").json()["retryable_hosts"] == [
            "192.168.56.11"
        ]
        url = f"/api/live-scans/{document.scan_id}/retry-hosts"
        assert client.post(url, json={"expected_revision": document.revision}).status_code == 403
        assert (
            client.post(
                url, headers=headers, json={"expected_revision": document.revision + 1}
            ).status_code
            == 409
        )
        assert not calls
        assert (
            client.post(
                url, headers=headers, json={"expected_revision": document.revision}
            ).status_code
            == 202
        )
        assert calls[0][0].hosts == ["192.168.56.11"]
        assert calls[0][0].profile == "light" and calls[0][1] == document.scan_id
        assert primary.read_bytes() == before


@pytest.mark.parametrize(
    "mapping",
    [
        None,
        [],
        [{}],
        [{"nodes": []}],
        [{"nodes": [{"cpeMatch": []}]}],
        [{"nodes": None}],
        [{"cpeMatch": [None]}],
    ],
)
@pytest.mark.asyncio
async def test_unusable_applicability_is_unknown_not_no_matches(mapping):
    record = {"id": "CVE-2026-10001", "descriptions": [], "configurations": mapping}
    data = {"totalResults": 1, "vulnerabilities": [{"cve": record}]}
    value = await NvdClient(httpx.MockTransport(lambda _: httpx.Response(200, json=data))).lookup(
        software(cpes=["cpe:/a:apache:http_server"])
    )
    assert value.related_status == "coverage_unknown" and value.related_unverified == 1
    assert not value.related_results


def test_exhausted_graph_is_unknown_but_usable_nonmatch_is_not_related():
    node = {"cpeMatch": [{"vulnerable": True, "criteria": PRODUCT}]}
    for _ in range(201):
        node = {"nodes": [node]}
    assert product_applicability({"configurations": [node]}, PRODUCT) == "unknown"
    other = PRODUCT.replace("apache", "different")
    assert (
        product_applicability(
            {"configurations": [{"cpeMatch": [{"vulnerable": True, "criteria": other}]}]}, PRODUCT
        )
        == "not_related"
    )
    assert (
        product_applicability(
            {
                "configurations": [
                    {"negate": True, "cpeMatch": [{"vulnerable": True, "criteria": PRODUCT}]}
                ]
            },
            PRODUCT,
        )
        == "not_related"
    )


@pytest.mark.parametrize(
    "payload,status",
    [
        ({"status": "found", "name": "Example.local"}, "found"),
        ({"status": "not_found"}, "not_found"),
        ({"status": "error"}, "error"),
        ({"status": "found", "name": []}, "not_found"),
    ],
)
@pytest.mark.asyncio
async def test_dns_worker_contract_and_private_boundaries(payload, status):
    calls = []

    async def runner(args, timeout_s, **kwargs):
        calls.append((args, timeout_s, kwargs))
        return ProcessResult(json.dumps(payload).encode(), b"", 0, 0)

    resolver = ReverseDnsResolver(runner=runner)
    value = await resolver.lookup("192.168.56.10")
    assert value.diagnostic.status == status and value.diagnostic.elapsed_ms >= 0
    assert value.hostname == ("Example.local" if status == "found" else None)
    assert calls[0][0][:3] == [sys.executable, "-I", "-c"]
    assert calls[0][2]["stdout_limit"] == 2048
    for ip in ("127.0.0.1", "8.8.8.8", "::1", "not-an-address"):
        with pytest.raises(ValueError):
            await resolver.lookup(ip)
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_blocked_name_workers_do_not_occupy_json_executor_and_are_reaped(tmp_path):
    async def sleeper(args, timeout_s, **kwargs):
        return await run_process(
            [sys.executable, "-I", "-c", "import time; time.sleep(30)"], timeout_s, **kwargs
        )

    resolver = ReverseDnsResolver(workers=2, timeout_s=0.15, runner=sleeper)
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        loop.set_default_executor(executor)
        tasks = [asyncio.create_task(resolver.lookup("192.168.56.10")) for _ in range(2)]
        try:
            store = JsonStore(tmp_path)
            doc = ScanDocument(scan_id=str(uuid4()), target={"mode": "demo"})
            await asyncio.wait_for(store.create_scan(doc), 1)
            assert (await asyncio.wait_for(store.load_scan(doc.scan_id), 1)).scan_id == doc.scan_id
            values = await asyncio.wait_for(asyncio.gather(*tasks), 5)
            assert all(value.diagnostic.status == "timeout" for value in values)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_name_queue_and_cancellation_are_bounded_and_release_admission():
    entered, finish = asyncio.Event(), asyncio.Event()

    async def runner(*args, **kwargs):
        entered.set()
        await finish.wait()
        return ProcessResult(b'{"status":"not_found"}', b"", 0, 0)

    resolver = ReverseDnsResolver(workers=1, queue_timeout_s=0.01, runner=runner)
    task = asyncio.create_task(resolver.lookup("192.168.56.10"))
    await entered.wait()
    assert (await resolver.lookup("192.168.56.11")).diagnostic.status == "busy"
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    finish.set()
    assert (await resolver.lookup("192.168.56.12")).diagnostic.status == "not_found"


def test_build_identity_is_deterministic_and_source_sensitive(tmp_path):
    (tmp_path / "code.py").write_text("pass\n")
    initial = source_build_id(tmp_path)
    assert source_build_id(tmp_path) == initial
    (tmp_path / "private.json").write_text("{}")
    assert source_build_id(tmp_path) == initial
    (tmp_path / "code.py").write_text("x=1\n")
    assert source_build_id(tmp_path) != initial


def test_build_headers_and_source_changed_status_do_not_expose_paths(monkeypatch):
    monkeypatch.setattr("app.api.session.nmap_preflight", lambda _: (True, "synthetic"))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda _: [])
    monkeypatch.setattr("app.api.session.source_build_id", lambda: "changed")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        authenticate_client(client, manager)
        reply = client.get("/api/status")
        assert reply.headers["X-NetGuard-Contract"] == str(API_CONTRACT_VERSION)
        data = reply.json()["build"]
        assert data["source_changed"] is True and data["build_id"] != "changed"
        assert set(data) == {"build_id", "contract_version", "started_at", "source_changed"}


def test_cve_completion_receipts_survive_other_tab_cache_hits_and_are_bounded():
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        service = software()
        doc = ScanDocument(
            scan_id=str(uuid4()),
            phase="finished",
            state="completed",
            target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
            services=[service],
        )
        client.app.state.store._create_scan(doc)
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(
                200,
                json={"totalResults": 0, "vulnerabilities": []}
                if "virtualMatchString" in request.url.params
                else nvd_data(),
            )

        client.app.state.nvd = NvdClient(httpx.MockTransport(handler))
        client.app.state.nvd.request_interval_s = 0
        client.app.state.explanations.provider = CveProvider()
        headers = authenticate_client(client, manager)
        path = f"/api/live-scans/{doc.scan_id}/services/{service.service_id}/cves"
        operations = [str(uuid4()) for _ in range(10)]
        checked = None
        for operation in operations:
            response = client.post(path, headers=headers, json={"operation_id": operation})
            assert response.status_code == 200
            value = response.json()["lookup"]
            checked = checked or value["checked_at"]
            assert value["checked_at"] == checked
        saved = client.get(f"/api/live-scans/{doc.scan_id}/annotations").json()["cve_lookups"][0]
        assert [item["operation_id"] for item in saved["operation_receipts"]] == operations[-8:]
        assert len(calls) == 2
