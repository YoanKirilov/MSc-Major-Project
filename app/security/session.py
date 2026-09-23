from __future__ import annotations

import secrets
from hashlib import sha256
from time import monotonic

from fastapi import HTTPException, Request


class SessionManager:
    def __init__(self, session_ttl_s: float = 8 * 60 * 60) -> None:
        self.bootstrap_token = secrets.token_urlsafe(32)
        self.csrf_secret = secrets.token_urlsafe(32)
        self.session_ttl_s = session_ttl_s
        self.sessions: dict[str, float] = {}

    def get_bootstrap_url(self, port: int) -> str:
        return f"http://127.0.0.1:{port}/#token={self.bootstrap_token}"

    def build_session_cookie(self) -> str:
        return secrets.token_urlsafe(32)

    def register_session(self) -> str:
        now = monotonic()
        self.sessions = {
            session_id: expires_at
            for session_id, expires_at in self.sessions.items()
            if expires_at > now
        }
        session_id = self.build_session_cookie()
        self.sessions[session_id] = now + self.session_ttl_s
        return session_id

    def csrf_for_session(self, session_id: str) -> str:
        return sha256(f"{session_id}:{self.csrf_secret}".encode("utf-8")).hexdigest()

    def validate_bootstrap(self, token: str | None) -> bool:
        if not isinstance(token, str):
            return False
        return secrets.compare_digest(token, self.bootstrap_token)

    def validate_session(self, request: Request) -> bool:
        session_cookie = request.cookies.get("session_id")
        if not session_cookie:
            return False
        expires_at = self.sessions.get(session_cookie)
        if expires_at is None:
            return False
        if expires_at <= monotonic():
            self.sessions.pop(session_cookie, None)
            return False
        return True

    def validate_csrf(self, request: Request) -> bool:
        token = request.headers.get("X-CSRF-Token")
        if not token:
            return False
        session_cookie = request.cookies.get("session_id")
        if not session_cookie:
            return False
        expected = self.csrf_for_session(session_cookie)
        return secrets.compare_digest(token, expected)

    def validate_request_boundary(self, request: Request, require_csrf: bool = False) -> None:
        port = request.app.state.config.port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
        if request.headers.get("host") not in allowed_hosts:
            raise HTTPException(status_code=403, detail="Invalid host")
        if request.method in {"POST", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            allowed_origins = {
                f"http://127.0.0.1:{port}",
                f"http://localhost:{port}",
                f"http://[::1]:{port}",
            }
            if origin not in allowed_origins:
                raise HTTPException(status_code=403, detail="Invalid origin")
            content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
            if content_type != "application/json":
                raise HTTPException(status_code=415, detail="Unsupported content type")
            if require_csrf and not self.validate_csrf(request):
                raise HTTPException(status_code=403, detail="CSRF validation failed")

    def authenticate(self, request: Request, require_csrf: bool = False) -> None:
        self.validate_request_boundary(request, require_csrf=require_csrf)
        if not self.validate_session(request):
            raise HTTPException(status_code=401, detail="Session required")
