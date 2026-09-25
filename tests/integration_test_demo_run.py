from app.main import create_app
from app.security.session import SessionManager
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client


def test_demo_run_button_endpoint_persists_result(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        response = client.post("/api/demo-runs", json={}, headers=headers)
        assert response.status_code == 201
        run_id = response.json()["run_id"]
        loaded = client.get(f"/api/demo-runs/{run_id}")

    assert loaded.status_code == 200
    assert loaded.json()["source"] == "demo"
    assert loaded.json()["result"]["mode"] == "demo"
    assert (tmp_path / "demo-runs" / f"{run_id}.json").exists()
