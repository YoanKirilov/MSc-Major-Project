"""Deferred regressions for configuration only; no real Pi-hole calls."""

import pytest
from app.config import AppConfig
from app.main import create_app
from app.security.session import SessionManager
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client


def test_password_file_accepts_windows_utf8_bom_and_trailing_newline(tmp_path, monkeypatch):
    secret = tmp_path / "application-password.txt"
    secret.write_bytes(b"\xef\xbb\xbfsynthetic-password\r\n")
    monkeypatch.setenv("APP_PIHOLE_PASSWORD_FILE", str(secret))
    config = AppConfig.from_env()
    assert config.pihole_password == "synthetic-password"
    assert config.pihole_configuration_error is None
    assert "synthetic-password" not in repr(config)
    assert str(secret) not in repr(config)


@pytest.mark.parametrize("contents", [b"", b"\n", b"x" * 4097, b"\xff", b"a\nb", b"a\x00b"])
def test_invalid_password_file_disables_connector_without_exposing_contents(
    contents, tmp_path, monkeypatch
):
    secret = tmp_path / "private-password.txt"
    secret.write_bytes(contents)
    monkeypatch.setenv("APP_PIHOLE_PASSWORD_FILE", str(secret))
    config = AppConfig.from_env()
    assert config.pihole_password is None
    assert config.pihole_configuration_error
    assert str(secret) not in config.pihole_configuration_error


def test_conflicting_password_sources_are_not_silently_selected(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_PIHOLE_PASSWORD", "synthetic-password")
    monkeypatch.setenv("APP_PIHOLE_PASSWORD_FILE", str(tmp_path / "missing.txt"))
    config = AppConfig.from_env()
    assert config.pihole_password is None
    assert "Set only one" in config.pihole_configuration_error
    assert "synthetic-password" not in repr(config)


def test_missing_password_file_is_a_sanitised_configuration_error(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_PIHOLE_PASSWORD_FILE", str(tmp_path / "private-missing.txt"))
    config = AppConfig.from_env()
    assert config.pihole_password is None
    assert "missing" in config.pihole_configuration_error
    assert "private-missing.txt" not in config.pihole_configuration_error


@pytest.mark.parametrize(
    ("url", "password", "configured", "has_error"),
    [
        ("http://127.0.0.1:8081", "synthetic-password", True, False),
        ("http://127.0.0.1:8081", "", False, True),
        ("", "synthetic-password", False, True),
        ("https://example.com/admin", "synthetic-password", False, True),
        ("", "", False, False),
    ],
)
def test_setup_status_is_local_only_and_never_exposes_credentials(
    url, password, configured, has_error, monkeypatch
):
    monkeypatch.setenv("APP_PIHOLE_URL", url)
    monkeypatch.setenv("APP_PIHOLE_PASSWORD", password)
    monkeypatch.setenv("APP_AI_PROVIDER", "none")
    monkeypatch.setattr("app.api.session.nmap_preflight", lambda config: (False, None))
    monkeypatch.setattr("app.api.session.nmap_interface_choices", lambda config: [])

    async def forbidden(*args, **kwargs):
        raise AssertionError("Viewing/saving configuration must not contact Pi-hole")

    monkeypatch.setattr("app.scanner.pihole.PiholeClient.names", forbidden)
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        assert client.get("/api/status").status_code == 401
        headers = authenticate_client(client, manager)
        status = client.get("/api/status")
        assert status.status_code == 200
        assert status.json()["pihole_configured"] is configured
        assert bool(status.json()["pihole_configuration_error"]) is has_error
        assert "synthetic-password" not in status.text
        settings = client.get("/api/settings").json()
        saved = client.patch(
            "/api/settings",
            headers=headers,
            json={"pihole_enabled": True, "expected_revision": settings["revision"]},
        )
        assert saved.status_code == (200 if configured else 422)
        assert "synthetic-password" not in saved.text
