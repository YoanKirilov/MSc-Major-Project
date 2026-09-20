from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import load_config
from .risk.engine import RiskEngine
from .storage.json_store import JsonStore
from .security.session import SessionManager
from .jobs.supervisor import ScanSupervisor
from .api import session as session_api
from .api import scans as scans_api
from .api import settings as settings_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    data_dir = Path(config.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    app.state.config = config
    app.state.store = JsonStore(data_dir)
    app.state.risk = RiskEngine()
    app.state.session_manager = SessionManager()
    app.state.supervisor = ScanSupervisor(app.state.store, nmap_path=config.nmap_path or "nmap")
    try:
        yield
    finally:
        await app.state.supervisor.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Network Assessor", lifespan=lifespan)
    app.state.response_factory = JSONResponse
    templates = Jinja2Templates(directory="app/templates")
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/")
    async def home(request):
        return templates.TemplateResponse("dashboard.html", {"request": request})

    @app.get("/settings")
    async def settings_page(request):
        return templates.TemplateResponse("settings.html", {"request": request})

    @app.get("/scans/{scan_id}")
    async def scan_page(request, scan_id: str):
        return templates.TemplateResponse("scan.html", {"request": request, "scan_id": scan_id})

    app.include_router(session_api.router)
    app.include_router(scans_api.router)
    app.include_router(settings_api.router)

    return app
