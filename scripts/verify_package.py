"""Run with the wheel environment's Python -I to avoid importing the checkout."""

import os
import tempfile
from pathlib import Path

import app
from app.main import create_app
from app.security.session import SessionManager
from fastapi.testclient import TestClient


def main():
    installed = Path(app.__file__).resolve().parent
    if "site-packages" not in str(installed):
        raise RuntimeError("Verification imported the checkout rather than the installed wheel")
    with tempfile.TemporaryDirectory(prefix="netguard-package-") as temporary:
        os.environ["APP_DATA_DIR"] = temporary
        os.environ["APP_PORT"] = "8765"
        manager = SessionManager()
        base = "http://127.0.0.1:8765"
        with TestClient(create_app(session_manager=manager), base_url=base) as client:
            for route in (
                "/",
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
            assets = [path for path in (installed / "static").rglob("*") if path.is_file()]
            for asset in assets:
                url = "/static/" + asset.relative_to(installed / "static").as_posix()
                assert client.get(url).status_code == 200, url
    print(
        f"Installed wheel passed: four pages, {len(assets)} static assets "
        "and demo read/create/reopen."
    )


if __name__ == "__main__":
    main()
