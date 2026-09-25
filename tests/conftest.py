import pytest


@pytest.fixture(autouse=True)
def isolate_application_data(tmp_path, monkeypatch):
    """Tests must never reconcile or write the developer's saved scans."""
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path / "app-data"))


@pytest.fixture(autouse=True)
def no_dns_in_offline_tests(request, monkeypatch):
    if request.node.get_closest_marker("live_lab"):
        return

    async def no_hostname(self, ip):
        return None

    monkeypatch.setattr("app.jobs.supervisor.ScanSupervisor._local_hostname", no_hostname)
    # API tests use synthetic scopes, never the developer's current Wi-Fi.
    monkeypatch.setattr("app.api.scans.detect_private_network", lambda: None)
    monkeypatch.setattr("app.api.session.detect_private_network", lambda: None)
