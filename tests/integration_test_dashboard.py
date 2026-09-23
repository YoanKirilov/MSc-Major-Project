import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from fastapi.testclient import TestClient

from app.main import create_app


def test_dashboard_uses_local_demo_adapter():
    with TestClient(create_app()) as client:
        page = client.get("/")
        demo = client.get("/api/demo-findings")

    assert page.status_code == 200
    assert "/static/css/app.css" in page.text
    assert "/static/js/dashboard.js" in page.text
    assert "if ('backend' !== 'backend')" in page.text
    assert 'id="scopeInput"' not in page.text
    assert 'id="deepHostInput"' in page.text
    assert demo.status_code == 200
    assert demo.json()["mode"] == "demo"
    assert len(demo.json()["findings"]) == 8


def test_scan_page_keeps_live_data_hooks_with_prototype_controls():
    with TestClient(create_app()) as client:
        page = client.get("/scans/11111111-1111-1111-1111-111111111111")

    assert page.status_code == 200
    assert 'id="searchInput"' in page.text
    assert 'data-filter="high"' in page.text
    assert 'id="nextStepsList"' in page.text
    assert 'id="device-table-body"' in page.text
    assert "if ('backend' !== 'backend')" in page.text
    assert "Safe checks" in page.text


def test_templates_and_static_assets_do_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.chdir(tmp_path)
    with TestClient(create_app()) as client:
        page = client.get("/")
        stylesheet = client.get("/static/css/app.css")

    assert page.status_code == 200
    assert stylesheet.status_code == 200


def test_active_pages_load_all_static_assets_and_module_dependencies(tmp_path, monkeypatch):
    """Catch missing assets after cleanup, including imports not directly in HTML."""
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path / "data"))

    class Assets(HTMLParser):
        def __init__(self):
            super().__init__()
            self.urls = set()

        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in {"src", "href"} and value and value.startswith("/static/"):
                    self.urls.add(value)

    assets = Assets()
    visited = set()
    with TestClient(create_app()) as client:
        for route, script in [
            ("/", "dashboard.js"),
            ("/scans/11111111-1111-1111-1111-111111111111", "scan.js"),
            ("/settings", "settings.js"),
        ]:
            page = client.get(route)
            assert page.status_code == 200
            assert f'/static/js/{script}' in page.text
            assert "{%" not in page.text
            assets.feed(page.text)

        pending = list(assets.urls)
        while pending:
            url = pending.pop()
            if url in visited:
                continue
            visited.add(url)
            response = client.get(url)
            assert response.status_code == 200, url
            if url.endswith((".js", ".mjs")):
                assert "javascript" in response.headers["content-type"], url
                for module in re.findall(r"\bfrom\s+['\"]([^'\"]+)['\"]", response.text):
                    pending.append(urljoin(url, module))

    static_root = Path(__file__).resolve().parents[1] / "app" / "static"
    actual_assets = {f"/static/{path.relative_to(static_root).as_posix()}"
                     for path in static_root.rglob("*") if path.is_file()}
    assert visited == actual_assets
