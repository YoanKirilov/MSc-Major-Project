"""Run with the wheel environment's Python -I to avoid importing the checkout."""

import os
import tempfile
from importlib import import_module
from pathlib import Path
from uuid import uuid4

import app
from app.main import create_app
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from fastapi.testclient import TestClient


def main():
    installed = Path(app.__file__).resolve().parent
    if "site-packages" not in str(installed):
        raise RuntimeError("Verification imported the checkout rather than the installed wheel")
    for name in (
        "app.jobs.enrichment",
        "app.scanner.observations",
        "app.profiling.history",
        "app.schemas.report_management",
        "app.storage.report_trash",
    ):
        module = import_module(name)
        assert Path(module.__file__).resolve().is_relative_to(installed), name
    with tempfile.TemporaryDirectory(prefix="netguard-package-") as temporary:
        os.environ["APP_DATA_DIR"] = temporary
        os.environ["APP_PORT"] = "8765"
        manager = SessionManager()
        base = "http://127.0.0.1:8765"
        with TestClient(create_app(session_manager=manager), base_url=base) as client:
            for route in (
                "/",
                "/light",
                "/deep",
                "/settings",
                "/history",
                "/scans/11111111-1111-1111-1111-111111111111",
            ):
                response = client.get(route)
                assert response.status_code == 200, route
                assert "{%" not in response.text, route
            assert client.get("/api/demo-findings").status_code == 200
            session = client.post(
                "/api/session", json={"token": manager.bootstrap_token}, headers={"Origin": base}
            )
            headers = {"Origin": base, "X-CSRF-Token": session.json()["csrf_token"]}
            created = client.post("/api/demo-runs", json={}, headers=headers)
            assert created.status_code == 201
            assert client.get("/api/demo-runs/" + created.json()["run_id"]).status_code == 200
            # Create a finished synthetic record, never start a network scan.
            report = ScanDocument(
                scan_id=str(uuid4()),
                state="completed",
                phase="finished",
                policy={"profile": "light"},
                target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
            )
            saved = client.portal.call(client.app.state.store.create_scan, report)
            listing = client.get("/api/reports?limit=24").json()
            item = listing["items"][0]
            assert item["scan_id"] == report.scan_id and item["deletable"] is True
            removed = client.post(
                "/api/reports/delete",
                json={
                    "reports": [
                        {
                            "scan_id": saved.scan_id,
                            "expected_revision": item["revision"],
                            "expected_notes_revision": item["expected_notes_revision"],
                        }
                    ]
                },
                headers=headers,
            )
            assert removed.status_code == 200 and removed.json()["deleted_count"] == 1
            assert client.get("/api/reports?limit=24").json()["total"] == 0
            recovery = client.get("/api/reports/recovery").json()
            assert recovery["total"] == 1 and recovery["items"][0]["restorable"] is True
            assert client.get("/api/storage-usage").json()["recovery_bytes"] > 0
            assert client.get("/api/report-capabilities").json()["management_version"] == 2
            restored = client.post(
                "/api/reports/restore",
                json={"trash_ids": [removed.json()["results"][0]["trash_id"]]},
                headers=headers,
            )
            assert restored.status_code == 200 and restored.json()["restored_count"] == 1
            assert client.get("/api/reports?limit=24").json()["total"] == 1
            assets = [path for path in (installed / "static").rglob("*") if path.is_file()]
            for asset in assets:
                url = "/static/" + asset.relative_to(installed / "static").as_posix()
                assert client.get(url).status_code == 200, url
    print(
        f"Installed wheel passed: six pages, {len(assets)} static assets "
        "and synthetic demo/report create/reopen/delete/Undo."
    )


if __name__ == "__main__":
    main()
