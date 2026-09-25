import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import require_session
from app.config import nmap_interface_choices
from app.scanner.mdns import mdns_available
from app.schemas.settings import SettingsUpdate

router = APIRouter(prefix="/api")


@router.get("/settings")
async def get_settings(request: Request):
    require_session(request)
    settings = await request.app.state.store.load_settings()
    return settings.model_copy(update={"ai_enabled": True})


@router.patch("/settings")
async def update_settings(request: Request, update: SettingsUpdate):
    require_session(request, csrf=True)
    if update.ai_enabled is False:
        raise HTTPException(
            status_code=422, detail="Ollama report preparation is required for every live scan."
        )
    if update.pihole_enabled and request.app.state.pihole is None:
        raise HTTPException(
            status_code=422,
            detail=request.app.state.pihole_configuration_error
            or (
                "Configure APP_PIHOLE_URL and APP_PIHOLE_PASSWORD_FILE "
                "(or APP_PIHOLE_PASSWORD) on the server, then restart the app."
            ),
        )
    if update.mdns_enabled and not mdns_available():
        raise HTTPException(status_code=503, detail="Optional mDNS discovery is not installed")
    if update.interface is not None:
        choices = await asyncio.to_thread(nmap_interface_choices, request.app.state.config)
        if update.interface not in choices:
            raise HTTPException(status_code=422, detail="Selected interface is unavailable")
    try:
        return await request.app.state.store.update_settings(update, update.expected_revision)
    except ValueError as exc:
        if str(exc) == "revision conflict":
            raise HTTPException(
                status_code=409, detail="Settings changed; reload and try again"
            ) from exc
        raise
