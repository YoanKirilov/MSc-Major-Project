import pytest
from app.main import create_app
from fastapi.testclient import TestClient


def test_second_instance_cannot_reconcile_shared_data_and_lock_is_released(monkeypatch):
    recovered = []

    async def reconcile(self):
        recovered.append(self)

    monkeypatch.setattr("app.jobs.supervisor.ScanSupervisor.reconcile_incomplete", reconcile)
    with TestClient(create_app()):
        assert len(recovered) == 1
        with pytest.raises(RuntimeError, match="already using this data folder"):
            with TestClient(create_app()):
                pass
        assert len(recovered) == 1
    with TestClient(create_app()):
        assert len(recovered) == 2


def test_failed_startup_releases_instance_lock(monkeypatch):
    async def fail(self):
        raise RuntimeError("synthetic startup failure")

    monkeypatch.setattr("app.jobs.supervisor.ScanSupervisor.reconcile_incomplete", fail)
    for _ in range(2):
        with pytest.raises(RuntimeError, match="synthetic startup failure"):
            with TestClient(create_app()):
                pass
