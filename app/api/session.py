from __future__ import annotations

import asyncio
from time import monotonic

from fastapi import APIRouter, HTTPException, Request

from app.config import (
    detect_private_network,
    network_warning,
    nmap_interface_choices,
    nmap_preflight,
    resolve_allowed_network,
)
from app.scanner.mdns import mdns_available
from app.security.session import SessionManager

router = APIRouter(prefix="/api")


def get_session_manager(request: Request) -> SessionManager:
    return request.app.state.session_manager


@router.post("/session")
async def create_session(request: Request):
    manager = get_session_manager(request)
    manager.validate_request_boundary(request)
    try:
        body = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
    token = body.get("token") if isinstance(body, dict) else None
    if not manager.validate_bootstrap(token):
        raise HTTPException(status_code=401, detail="Invalid bootstrap token")
    session_id = manager.register_session()
    csrf_token = manager.csrf_for_session(session_id)
    response = {"csrf_token": csrf_token}
    response_obj = request.app.state.response_factory(response)
    response_obj.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        samesite="strict",
        path="/",
        max_age=int(manager.session_ttl_s),
    )
    return response_obj


@router.get("/session")
async def get_session(request: Request):
    manager = request.app.state.session_manager
    manager.validate_request_boundary(request)
    if not manager.validate_session(request):
        raise HTTPException(status_code=401, detail="Session required")
    session = request.cookies["session_id"]
    return {"csrf_token": manager.csrf_for_session(session)}


@router.get("/status")
async def status(request: Request):
    request.app.state.session_manager.authenticate(request)
    config = request.app.state.config
    settings = await request.app.state.store.load_settings()
    storage_ok = await asyncio.to_thread(request.app.state.store.storage_writable)
    async with request.app.state.runtime_status_lock:
        runtime = request.app.state.runtime_status_cache
        if runtime is None or monotonic() - runtime["checked_at"] > 30:
            scanner_result, interfaces, ai_available = await asyncio.gather(
                asyncio.to_thread(nmap_preflight, config),
                asyncio.to_thread(nmap_interface_choices, config),
                request.app.state.explanations.provider_available(),
            )
            scanner_available, scanner_version = scanner_result
            runtime = {
                "checked_at": monotonic(),
                "scanner_available": scanner_available,
                "scanner_version": scanner_version,
                "interface_choices": interfaces,
                "ai_available": ai_available,
            }
            request.app.state.runtime_status_cache = runtime
    supervisor = request.app.state.supervisor
    active_scan_ids = supervisor.active_scan_ids
    detected = await asyncio.to_thread(detect_private_network)
    scope = settings.allowed_network or resolve_allowed_network(config, detected)
    return {
        "app_version": "0.1.0",
        "scanner_available": runtime["scanner_available"],
        "scanner_version": runtime["scanner_version"],
        "interface_choices": runtime["interface_choices"],
        "ai_configured": config.ai_provider == "ollama" and bool(config.ai_model),
        "ai_available": runtime["ai_available"],
        "ai_enabled": True,
        "ai_required": True,
        "pihole_configured": request.app.state.pihole is not None,
        "pihole_enabled": settings.pihole_enabled,
        "ai_provider": config.ai_provider,
        "ai_model": config.ai_model,
        "mdns_available": mdns_available(),
        "mdns_enabled": settings.mdns_enabled,
        "allowed_network": scope,
        "detected_network": detected,
        "network_warning": network_warning(scope, detected),
        "active_scan_id": active_scan_ids[0] if len(active_scan_ids) == 1 else None,
        "active_scan_ids": list(active_scan_ids),
        "active_scan_count": len(active_scan_ids),
        "max_concurrent_scans": supervisor.max_concurrent_scans,
        "storage_status": "ok" if storage_ok else "not_writable",
    }
