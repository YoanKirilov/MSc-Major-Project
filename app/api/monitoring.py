"""Local, authenticated opt-in periodic Light checks."""

from fastapi import APIRouter, Request

from app.api.dependencies import require_session
from app.storage.monitoring import MonitoringUpdate

router = APIRouter(prefix="/api")


@router.get("/monitoring")
async def monitoring_status(request: Request):
    require_session(request)
    return await request.app.state.monitoring.status()


@router.put("/monitoring")
async def configure_monitoring(request: Request, body: MonitoringUpdate):
    require_session(request, csrf=True)
    return await request.app.state.monitoring.configure(body)
