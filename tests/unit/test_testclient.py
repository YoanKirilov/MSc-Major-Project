"""Ensure API tests use Starlette's supported client without hiding warnings."""

import httpx2
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_supported_client_handles_requests():
    app = FastAPI()

    @app.get("/check")
    def check():
        return {"ok": True}

    with TestClient(app) as client:
        assert isinstance(client, httpx2.Client)
        assert client.get("/check").json() == {"ok": True}
