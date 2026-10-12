from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.main import create_app
from app.security.session import SessionManager
from fastapi.testclient import TestClient
from filelock import Timeout
from tests.session_helpers import BASE_URL, authenticate_client


@pytest.mark.parametrize(
    ("route", "method"),
    [("scans", "load_scan"), ("live-scans", "load_scan"), ("live-scans/progress", "load_progress")],
)
@pytest.mark.parametrize(
    ("error", "status", "text"),
    [
        (OSError("private path must not leak"), 503, "do not start another scan"),
        (FileNotFoundError("private path"), 404, "not found"),
        (ValueError("invalid saved JSON"), 404, "not found"),
        (PermissionError("private path"), 503, "normal user permissions"),
        (Timeout("private lock path"), 503, "busy"),
    ],
)
def test_saved_read_failure_is_specific_retryable_and_never_resubmits(
    tmp_path, monkeypatch, route, method, error, status, text
):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    manager = SessionManager()
    app = create_app(session_manager=manager)
    scan_id = str(uuid4())
    path = (
        f"/api/live-scans/{scan_id}/progress"
        if route.endswith("/progress")
        else f"/api/{route}/{scan_id}"
    )
    with TestClient(app, base_url=BASE_URL, raise_server_exceptions=False) as client:
        authenticate_client(client, manager)
        before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*.json")}
        read = AsyncMock(side_effect=error)
        start = AsyncMock()
        monkeypatch.setattr(app.state.store, method, read)
        monkeypatch.setattr(app.state.supervisor, "start", start)
        response = client.get(path)
        assert response.status_code == status
        assert text in response.json()["detail"]
        assert "private" not in response.text
        if type(error) is OSError:
            assert response.headers["Retry-After"] == "2"
        read.assert_awaited_once_with(scan_id)
        start.assert_not_awaited()
        assert {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*.json")} == before
