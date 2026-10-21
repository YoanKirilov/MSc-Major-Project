"""Response protections must be real headers, including error and static paths."""

import pytest
from app.main import create_app
from app.security.headers import LOCAL_RESPONSE_HEADERS
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL


def protected(response):
    for name, value in LOCAL_RESPONSE_HEADERS.items():
        assert response.headers[name] == value


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [
        ("GET", "/", 200),
        ("GET", "/settings", 200),
        ("GET", "/devices", 200),
        ("GET", "/history", 200),
        ("GET", "/scans/55555555-5555-4555-8555-555555555555", 200),
        ("GET", "/static/js/api.js", 200),
        ("HEAD", "/static/js/report.mjs", 200),
        ("GET", "/static/css/app.css", 200),
        ("GET", "/static/no-such-asset.js", 404),
        ("GET", "/no-such-page", 404),
        ("GET", "/docs", 404),
        ("GET", "/redoc", 404),
        ("GET", "/docs/oauth2-redirect", 404),
        ("POST", "/history", 405),
        ("GET", "/api/session", 401),
        ("POST", "/api/session", 403),
    ],
)
def test_normal_static_and_error_responses_have_security_headers(method, path, status):
    with TestClient(create_app(), base_url=BASE_URL) as client:
        response = client.request(method, path)
        assert response.status_code == status
        protected(response)
        if path == "/":
            assert 'http-equiv="Content-Security-Policy"' not in response.text
            assert 'http-equiv="X-Content-Type-Options"' not in response.text


def test_conditional_range_and_cookie_headers_are_not_broken():
    with TestClient(create_app(), base_url=BASE_URL) as client:
        original = client.get("/static/js/api.js")
        unchanged = client.get(
            "/static/js/api.js", headers={"If-None-Match": original.headers["etag"]}
        )
        partial = client.get("/static/js/api.js", headers={"Range": "bytes=0-9"})
        assert unchanged.status_code == 304 and unchanged.content == b""
        assert partial.status_code == 206 and partial.content == original.content[:10]
        assert partial.headers["content-type"] == "text/javascript; charset=utf-8"
        protected(unchanged)
        protected(partial)


def test_openapi_schema_remains_available_without_cdn_based_documentation():
    with TestClient(create_app(), base_url=BASE_URL) as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "/api/live-scans" in response.json()["paths"]
        protected(response)


def test_unexpected_server_error_is_protected_without_leaking_exception_details():
    app = create_app()

    @app.get("/synthetic-error")
    async def broken():
        raise RuntimeError("synthetic-private-exception-detail")

    with TestClient(app, base_url=BASE_URL, raise_server_exceptions=False) as client:
        response = client.get("/synthetic-error")
        assert response.status_code == 500
        protected(response)
        assert "synthetic-private-exception-detail" not in response.text
        assert response.json()["detail"].startswith("The local app encountered")


def test_response_protection_does_not_swallow_server_exceptions():
    app = create_app()

    @app.get("/synthetic-error")
    async def broken():
        raise RuntimeError("synthetic-observable-error")

    with TestClient(app, base_url=BASE_URL) as client:
        with pytest.raises(RuntimeError, match="synthetic-observable-error"):
            client.get("/synthetic-error")
