"""Removing automatic checks never removes or reactivates a person's old data."""

import os
from pathlib import Path

import pytest
from app.main import create_app
from app.security.session import SessionManager
from app.storage.backup import transfer
from fastapi.testclient import TestClient


@pytest.mark.parametrize("legacy", [False, True])
def test_no_periodic_runtime_routes_or_assets_and_legacy_bytes_are_preserved(legacy, monkeypatch):
    monkeypatch.setenv("APP_PORT", "8765")
    root = Path(os.environ["APP_DATA_DIR"])
    root.mkdir(parents=True)
    path = root / "monitor.json"
    backup = root / "monitor.previous.json"
    # These deliberately enabled settings are inert archival bytes, not authority
    # to start work on whichever network the person happens to be connected to.
    content = b'{"version":1,"enabled":true,"scope":"192.168.56.0/24"}\n'
    if legacy:
        path.write_bytes(content)
        backup.write_bytes(content + b" ")
    before = {item.name: item.read_bytes() for item in root.glob("monitor*")}
    manager = SessionManager()
    base = "http://127.0.0.1:8765"
    application = create_app(session_manager=manager)
    with TestClient(application, base_url=base) as client:
        session = client.post(
            "/api/session", json={"token": manager.bootstrap_token}, headers={"Origin": base}
        )
        assert session.status_code == 200
        headers = {"Origin": base, "X-CSRF-Token": session.json()["csrf_token"]}
        assert not hasattr(application.state, "monitoring")
        assert "/api/monitoring" not in client.get("/openapi.json").json()["paths"]
        assert client.get("/api/monitoring").status_code == 404
        assert (
            client.put("/api/monitoring", json={"enabled": True}, headers=headers).status_code
            == 404
        )
        for name in ("monitoring.js", "monitoring-model.mjs"):
            assert client.get(f"/static/js/{name}").status_code == 404
        settings = client.get("/settings").text
        assert "periodic" not in settings.lower()
        assert "monitor-form" not in settings
        assert "motionPreference" not in settings
        assert "textSizePreference" in settings and "themePreference" in settings
    assert {item.name: item.read_bytes() for item in root.glob("monitor*")} == before


def test_private_backup_keeps_removed_monitor_settings_only_as_archival_bytes(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    originals = {"monitor.json": b"legacy settings\n", "monitor.previous.json": b"older settings\n"}
    for name, content in originals.items():
        (source / name).write_bytes(content)
    backup = tmp_path / "backup"
    restored = tmp_path / "restored"
    assert transfer(source, backup)["verified"]
    assert transfer(backup, restored, restore=True)["verified"]
    for name, content in originals.items():
        assert (source / name).read_bytes() == content
        assert (backup / name).read_bytes() == content
        assert (restored / name).read_bytes() == content
