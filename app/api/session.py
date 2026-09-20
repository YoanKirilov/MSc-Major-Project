from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.config import load_config
from app.security.session import SessionManager

router = APIRouter(prefix="/api")


def get_session_manager(request: Request) -> SessionManager:
    return request.app.state.session_manager


@router.post("/session")
async def create_session(request: Request):
    body = await request.json()
    token = body.get("token")
    manager = get_session_manager(request)
    if not manager.validate_bootstrap(token):
        raise HTTPException(status_code=401, detail="Invalid bootstrap token")
    session_id = manager.build_session_cookie()
    manager.sessions[session_id] = session_id
    csrf_token = manager.csrf_for_session(session_id)
    response = {"csrf_token": csrf_token}
    response_obj = request.app.state.response_factory(response)
    response_obj.set_cookie("session_id", session_id, httponly=True, samesite="strict", path="/")
    return response_obj


@router.get("/session")
async def get_session(request: Request):
    session = request.cookies.get("session_id")
    if not session or session not in request.app.state.session_manager.sessions:
        raise HTTPException(status_code=401, detail="Session required")
    return {"csrf_token": request.app.state.session_manager.csrf_for_session(session)}


@router.get("/status")
async def status(request: Request):
    config = load_config()
    return {
        "app_version": "0.1.0",
        "scanner_available": False,
        "scanner_version": None,
        "interface_choices": ["eth0", "ens33", "lo"],
        "ai_configured": False,
        "ai_model": config.ai_model,
        "active_scan_id": None,
        "storage_status": "ok",
    }
