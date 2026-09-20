from fastapi import APIRouter, Request

from app.schemas.settings import SettingsUpdate

router = APIRouter(prefix="/api")


def require_session(request: Request, csrf: bool = False):
    request.app.state.session_manager.authenticate(request, require_csrf=csrf)


@router.get("/settings")
async def get_settings(request: Request):
    require_session(request)
    return await request.app.state.store.load_settings()


@router.patch("/settings")
async def update_settings(request: Request, update: SettingsUpdate):
    require_session(request, csrf=True)
    return await request.app.state.store.update_settings(update, update.expected_revision)
