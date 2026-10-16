"""Browser assets must not inherit a machine's incorrect extension associations."""

import mimetypes
from pathlib import Path

import pytest
from app.main import create_app
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL


@pytest.mark.parametrize("method", ["get", "head"])
@pytest.mark.parametrize(
    ("path", "media_type"),
    [
        ("js/api.js", "text/javascript"),
        ("js/report.mjs", "text/javascript"),
        ("css/app.css", "text/css"),
    ],
)
def test_static_asset_mime_does_not_depend_on_registry(path, media_type, method, monkeypatch):
    mimetypes.init()
    suffix = Path(path).suffix
    monkeypatch.setitem(mimetypes.types_map, suffix, "text/plain")
    assert mimetypes.guess_type(path)[0] == "text/plain"
    with TestClient(create_app(), base_url=BASE_URL) as client:
        response = getattr(client, method)(f"/static/{path}")
        assert response.status_code == 200
        assert response.headers["content-type"] == f"{media_type}; charset=utf-8"
        assert response.headers["cache-control"] == "no-store"
        assert bool(response.content) == (method == "get")
    # Serving this app must not rewrite the process/global MIME registry.
    assert mimetypes.guess_type(path)[0] == "text/plain"


def test_static_conditionals_ranges_and_missing_assets_keep_http_semantics(monkeypatch):
    mimetypes.init()
    monkeypatch.setitem(mimetypes.types_map, ".mjs", "text/plain")
    with TestClient(create_app(), base_url=BASE_URL) as client:
        url = "/static/js/report.mjs"
        original = client.get(url)
        unchanged = client.get(url, headers={"If-None-Match": original.headers["etag"]})
        assert unchanged.status_code == 304 and unchanged.content == b""
        partial = client.get(url, headers={"Range": "bytes=0-9"})
        assert partial.status_code == 206 and partial.content == original.content[:10]
        assert partial.headers["content-type"] == "text/javascript; charset=utf-8"
        multipart = client.get(url, headers={"Range": "bytes=0-1,8-9"})
        assert multipart.status_code == 206
        assert multipart.headers["content-type"].startswith("multipart/byteranges")
        assert b"content-type: text/javascript" in multipart.content.lower()
        missing = client.get("/static/js/no-such-asset.mjs")
        assert missing.status_code == 404
        assert "javascript" not in missing.headers.get("content-type", "")
        assert client.get("/static/%2e%2e/main.py").status_code == 404
