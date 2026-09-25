import pytest
from app.main import create_app
from app.schemas.scan import Device, Finding, ScanDocument, Service
from app.schemas.settings import SettingsUpdate
from app.security.session import SessionManager
from fastapi.testclient import TestClient
from tests.fixtures.fixtures import make_telnet_scan
from tests.session_helpers import BASE_URL, authenticate_client


@pytest.fixture(autouse=True)
def mock_provider_availability(monkeypatch):
    async def available(self):
        return True

    monkeypatch.setattr("app.explanations.service.OllamaExplanationProvider.available", available)


def test_live_scan_reports_missing_nmap_without_creating_fake_result(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (False, None))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: None)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post(
            "/api/live-scans",
            json={
                "mode": "known_hosts",
                "hosts": ["192.168.56.1"],
                "authorised": True,
            },
            headers=headers,
        )
    assert response.status_code == 503
    assert "Nmap" in response.json()["detail"]
    assert (
        not list((tmp_path / "scans").glob("*/scan.json"))
        if (tmp_path / "scans").exists()
        else True
    )


def test_live_scan_reports_unwritable_local_storage(tmp_path, monkeypatch):
    async def deny_scan_write(_document):
        raise PermissionError("private path must not reach the response")

    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "Nmap"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "nmap")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        monkeypatch.setattr(client.app.state.store, "create_scan", deny_scan_write)
        response = client.post(
            "/api/live-scans",
            json={
                "mode": "known_hosts",
                "hosts": ["192.168.56.1"],
                "authorised": True,
            },
            headers=headers,
        )

    assert response.status_code == 503
    assert "not writable" in response.json()["detail"]
    assert "private path" not in response.text


def test_live_scan_rejects_unknown_profile_before_creating_a_job(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "Nmap"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "nmap")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post(
            "/api/live-scans",
            json={
                "mode": "known_hosts",
                "hosts": ["192.168.56.1"],
                "profile": "unsupported",
                "authorised": True,
            },
            headers=headers,
        )
    assert response.status_code == 422
    assert "profile" in response.json()["detail"]
    assert (
        not list((tmp_path / "scans").glob("*/scan.json"))
        if (tmp_path / "scans").exists()
        else True
    )


def test_deep_scan_rejects_multiple_hosts_before_creating_a_job(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "Nmap"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "nmap")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post(
            "/api/live-scans",
            json={
                "mode": "known_hosts",
                "profile": "deep-tcp-v1",
                "hosts": ["192.168.56.1", "192.168.56.2"],
                "authorised": True,
            },
            headers=headers,
        )
    assert response.status_code == 422
    assert "exactly one" in response.json()["detail"]


def test_live_scan_reports_capacity_without_leaving_a_queued_scan(tmp_path, monkeypatch):
    async def reject_for_capacity(self, scan_id):
        raise RuntimeError("SCAN_CAPACITY")

    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "Nmap"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "nmap")
    monkeypatch.setattr("app.jobs.supervisor.ScanSupervisor.start", reject_for_capacity)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post(
            "/api/live-scans",
            json={
                "mode": "known_hosts",
                "hosts": ["192.168.56.1"],
                "authorised": True,
            },
            headers=headers,
        )
    assert response.status_code == 429
    assert "capacity" in response.json()["detail"].lower()
    assert not list((tmp_path / "scans").glob("*/scan.json"))


def test_client_cannot_override_server_owned_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post(
            "/api/live-scans",
            json={
                "mode": "known_hosts",
                "scope_cidr": "10.0.0.0/8",
                "hosts": ["10.0.0.2"],
                "authorised": True,
            },
            headers=headers,
        )

    assert response.status_code == 422
    assert (
        not list((tmp_path / "scans").glob("*/scan.json"))
        if (tmp_path / "scans").exists()
        else True
    )


def test_legacy_scan_route_uses_same_scope_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "Nmap"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "nmap")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post(
            "/api/scans",
            json={
                "mode": "known_hosts",
                "hosts": ["192.168.57.1"],
                "authorised": True,
            },
            headers=headers,
        )

    assert response.status_code == 422
    assert (
        not list((tmp_path / "scans").glob("*/scan.json"))
        if (tmp_path / "scans").exists()
        else True
    )


def test_saved_report_ai_endpoint_requires_provider_and_does_not_rescan(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        finding = Finding.model_validate(make_telnet_scan()["finding"])
        scan = ScanDocument(
            scan_id="74747474-7474-4747-8747-747474747474",
            state="completed",
            phase="finished",
            target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.56.10"]},
            findings=[finding],
        )
        client.app.state.store._create_scan(scan)

        async def unavailable():
            return False

        monkeypatch.setattr(client.app.state.explanations, "provider_available", unavailable)
        unavailable_response = client.post(
            f"/api/live-scans/{scan.scan_id}/explanations", json={}, headers=headers
        )
        assert unavailable_response.status_code == 503
        assert "Ollama" in unavailable_response.json()["detail"]

        client.app.state.store._update_settings(
            SettingsUpdate(expected_revision=1, ai_enabled=True), 1
        )
        missing_csrf = client.post(
            f"/api/live-scans/{scan.scan_id}/explanations",
            json={},
            headers={"Origin": BASE_URL},
        )
        assert missing_csrf.status_code == 403
        called = []

        async def available():
            return True

        async def no_rescan(scan_id):
            called.append(scan_id)

        monkeypatch.setattr(client.app.state.explanations, "provider_available", available)
        monkeypatch.setattr(client.app.state.supervisor, "request_explanations", no_rescan)
        accepted = client.post(
            f"/api/live-scans/{scan.scan_id}/explanations", json={}, headers=headers
        )
        assert accepted.status_code == 202
        assert called == [scan.scan_id]
        assert client.app.state.store._load_scan(scan.scan_id).findings == [finding]


def test_refresh_guidance_requires_csrf_preserves_evidence_and_does_not_rescan(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    manager = SessionManager()
    fixture = make_telnet_scan()
    scan = ScanDocument(
        scan_id="74747474-7474-4747-8747-747474747474",
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "cidr": None, "hosts": ["192.168.0.10"]},
        devices=[Device.model_validate(fixture["device"])],
        services=[Service.model_validate(fixture["service"])],
        findings=[Finding.model_validate(fixture["finding"])],
    )
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        client.app.state.store._create_scan(scan)

        async def forbidden(*args):
            raise AssertionError("Refreshing guidance must not scan or call AI")

        monkeypatch.setattr(client.app.state.supervisor, "start", forbidden)
        monkeypatch.setattr(client.app.state.explanations, "explain_scan", forbidden)
        url = f"/api/live-scans/{scan.scan_id}"
        assert client.get(url).json()["guidance_status"]["refresh_available"]
        assert (
            client.post(
                url + "/refresh-guidance",
                json={"expected_revision": 1},
                headers={"Origin": BASE_URL},
            ).status_code
            == 403
        )
        assert (
            client.post(
                url + "/refresh-guidance", json={"expected_revision": 99}, headers=headers
            ).status_code
            == 409
        )
        assert (
            client.post(
                url + "/refresh-guidance", json={"expected_revision": 1}, headers=headers
            ).status_code
            == 200
        )
        result = client.get(url).json()
        assert not result["guidance_status"]["refresh_available"]
        assert result["guidance_history"][0]["findings"] == [
            finding.model_dump(mode="json") for finding in scan.findings
        ]
        assert (
            result["findings"][0]["evidence"]
            == scan.findings[0].model_dump(mode="json")["evidence"]
        )
        assert result["devices"] == [device.model_dump(mode="json") for device in scan.devices]
        assert result["ai_requests_used"] == 0
        client.app.state.store._update_scan(
            scan.scan_id, lambda current: current.model_copy(update={"phase": "analysis"}), None
        )
        assert (
            client.post(
                url + "/refresh-guidance", json={"expected_revision": 3}, headers=headers
            ).status_code
            == 409
        )


def test_retry_checks_only_unfinished_hosts_and_revalidates_current_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_NETWORK", "192.168.56.0/24")
    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "test"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "test-nmap")

    async def record_start(self, scan_id):
        pass

    monkeypatch.setattr("app.jobs.supervisor.ScanSupervisor.start", record_start)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        original = ScanDocument(
            scan_id="84848484-8484-4848-8848-848484848484",
            state="partial",
            phase="finished",
            target={"mode": "discover", "cidr": "192.168.56.0/24", "hosts": []},
            policy={"profile": "light"},
            coverage={
                "targets": [
                    {
                        "ip": "192.168.56.10",
                        "discovery_status": "observed",
                        "service_status": "completed",
                    },
                    {
                        "ip": "192.168.56.11",
                        "discovery_status": "observed",
                        "service_status": "timed_out",
                    },
                    {
                        "ip": "192.168.56.12",
                        "discovery_status": "not_seen",
                        "service_status": "skipped",
                    },
                ]
            },
        )
        client.app.state.store._create_scan(original)
        url = f"/api/live-scans/{original.scan_id}/retry-hosts"
        assert (
            client.post(
                url, json={"expected_revision": 1}, headers={"Origin": BASE_URL}
            ).status_code
            == 403
        )
        response = client.post(url, json={"expected_revision": 1}, headers=headers)
        assert response.status_code == 202
        retried = client.app.state.store._load_scan(response.json()["scan_id"])
        assert retried.target["hosts"] == ["192.168.56.11"]
        assert retried.policy["retry_of"] == original.scan_id
        assert client.app.state.store._load_scan(original.scan_id) == original
        client.app.state.store._update_settings(
            SettingsUpdate(expected_revision=1, allowed_network="192.168.57.0/24"), 1
        )
        assert client.post(url, json={"expected_revision": 1}, headers=headers).status_code == 422
