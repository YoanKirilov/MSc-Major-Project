"""Shared authentication checks for local API routes."""

from fastapi import Request


def require_session(request: Request, csrf: bool = False) -> None:
    request.app.state.session_manager.authenticate(request, require_csrf=csrf)
