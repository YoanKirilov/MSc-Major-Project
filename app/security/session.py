from __future__ import annotations

import secrets
from hashlib import sha256
from typing import Literal

from fastapi import HTTPException, Request


class SessionManager:
    def __init__(self) -> None:
        self.bootstrap_token = secrets.token_urlsafe(32)
        self.session_secret = secrets.token_urlsafe(32)
        self.csrf_secret = secrets.token_urlsafe(32)
        self.sessions: dict[str, str] = {}

    def get_bootstrap_url(self, port: int) -> str:
        return f"http://127.0.0.1:{port}/#token={self.bootstrap_token}"

    def build_session_cookie(self) -> str:
        return secrets.token_urlsafe(32)

    def csrf_for_session(self, session_id: str) -> str:
        return sha256(f"{session_id}:{self.csrf_secret}".encode("utf-8")).hexdigest()

    def validate_bootstrap(self, token: str) -> bool:
        return secrets.compare_digest(token, self.bootstrap_token)

    def validate_session(self, request: Request) -> bool:
        session_cookie = request.cookies.get("session_id")
        if not session_cookie:
            return False
        return session_cookie in self.sessions

    def validate_csrf(self, request: Request) -> bool:
        token = request.headers.get("X-CSRF-Token")
        if not token:
            return False
        session_cookie = request.cookies.get("session_id")
        if not session_cookie:
            return False
        expected = self.csrf_for_session(session_cookie)
        return secrets.compare_digest(token, expected)

    def authenticate(self, request: Request, require_csrf: bool = False) -> None:
        if request.headers.get("host") not in {f"127.0.0.1:{request.app.state.config.port}", f"localhost:{request.app.state.config.port}"}:
            raise HTTPException(status_code=403, detail="Invalid host")
        if request.method in {"POST", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin not in {f"http://127.0.0.1:{request.app.state.config.port}"}:
                raise HTTPException(status_code=403, detail="Invalid origin")
            if request.headers.get("content-type", "").lower() != "application/json":
                raise HTTPException(status_code=415, detail="Unsupported content type")
            if require_csrf and not self.validate_csrf(request):
                raise HTTPException(status_code=403, detail="CSRF validation failed")
        if not self.validate_session(request):
            raise HTTPException(status_code=401, detail="Session required")
