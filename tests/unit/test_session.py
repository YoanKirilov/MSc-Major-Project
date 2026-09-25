from app.main import create_app
from app.security.session import SessionManager
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client


def test_missing_bootstrap_token_returns_401(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    with TestClient(create_app(), base_url=BASE_URL, raise_server_exceptions=False) as client:
        response = client.post("/api/session", json={}, headers={"Origin": BASE_URL})
    assert response.status_code == 401


def test_session_bootstrap_allows_status_and_requires_csrf(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        csrf_headers = authenticate_client(client, manager)
        assert client.get("/api/status").status_code == 200

        rejected = client.patch("/api/settings", json={"expected_revision": 1})
        accepted = client.patch(
            "/api/settings",
            json={"expected_revision": 1},
            headers=csrf_headers,
        )

    assert rejected.status_code == 403
    assert accepted.status_code == 200


def test_live_scan_endpoints_require_a_session(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    with TestClient(create_app(), base_url=BASE_URL) as client:
        create_response = client.post(
            "/api/live-scans",
            json={"mode": "known_hosts", "hosts": ["192.168.0.2"], "authorised": True},
            headers={"Origin": BASE_URL},
        )
        read_response = client.get("/api/live-scans/11111111-1111-4111-8111-111111111111")

    assert create_response.status_code == 403
    assert read_response.status_code == 401
