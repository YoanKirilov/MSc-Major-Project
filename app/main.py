from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from filelock import FileLock, Timeout

from .api import demo as demo_api
from .api import scans as scans_api
from .api import session as session_api
from .api import settings as settings_api
from .config import load_config, resolve_nmap_path
from .demo.adapter import DemoFindingsAdapter
from .demo.runs import DemoRunStore
from .explanations import ExplanationService, OllamaExplanationProvider
from .jobs.supervisor import ScanSupervisor
from .scanner.pihole import PiholeClient
from .security.session import SessionManager
from .storage.json_store import DocumentTooLarge, JsonStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Own the data folder before recovering jobs or touching persisted state.
    # An OS lock is released on process exit; a leftover file is not a stale lock.
    data_dir = Path(load_config().data_dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(data_dir / "app-instance.lock"), thread_local=False)
    try:
        lock.acquire(timeout=0)
    except Timeout as exc:
        raise RuntimeError(
            (
                "Network Assessor is already using this data folder. Use the "
                "existing app window or stop that instance before restarting."
            )
        ) from exc
    try:
        async with owned_lifespan(app):
            yield
    finally:
        lock.release()


@asynccontextmanager
async def owned_lifespan(app: FastAPI):
    config = load_config()
    data_dir = Path(config.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    app.state.config = config
    app.state.runtime_status_lock = asyncio.Lock()
    app.state.runtime_status_cache = None
    app.state.store = JsonStore(data_dir)
    app.state.storage_writable_at_startup = await asyncio.to_thread(
        app.state.store.storage_writable
    )
    app.state.session_manager = (
        getattr(app.state, "initial_session_manager", None) or SessionManager()
    )
    app.state.demo_data = DemoFindingsAdapter()
    app.state.demo_runs = DemoRunStore(data_dir / "demo-runs", app.state.demo_data)
    explanation_provider = None
    if config.ai_provider == "ollama":
        try:
            explanation_provider = OllamaExplanationProvider(
                model=config.ai_model,
                base_url=config.ai_base_url,
                timeout_s=config.ai_timeout_s,
            )
        except ValueError:
            explanation_provider = None
    app.state.explanations = ExplanationService(
        app.state.store,
        explanation_provider,
        enabled=True,
    )
    app.state.pihole = None
    app.state.pihole_configuration_error = config.pihole_configuration_error
    if not app.state.pihole_configuration_error and config.pihole_url and config.pihole_password:
        try:
            app.state.pihole = PiholeClient(config.pihole_url, config.pihole_password)
        except ValueError:
            app.state.pihole_configuration_error = (
                "Use a private or loopback IP HTTP(S) origin for APP_PIHOLE_URL, "
                "without credentials, an /admin path or an /api path."
            )
    elif not app.state.pihole_configuration_error and (config.pihole_url or config.pihole_password):
        app.state.pihole_configuration_error = (
            "Configure both APP_PIHOLE_URL and a Pi-hole password "
            "using APP_PIHOLE_PASSWORD_FILE or APP_PIHOLE_PASSWORD."
        )
    app.state.supervisor = ScanSupervisor(
        app.state.store,
        nmap_path=resolve_nmap_path(config) or "nmap",
        explanation_service=app.state.explanations,
        max_concurrent_scans=config.max_concurrent_scans,
        pihole_client=app.state.pihole,
    )
    await app.state.supervisor.reconcile_incomplete()
    try:
        yield
    finally:
        await app.state.supervisor.shutdown()


def create_app(*, session_manager: SessionManager | None = None) -> FastAPI:
    app = FastAPI(title="Network Assessor", lifespan=lifespan)
    app.state.initial_session_manager = session_manager
    app.state.response_factory = JSONResponse
    app_root = Path(__file__).resolve().parent
    templates = Jinja2Templates(directory=str(app_root / "templates"))
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=str(app_root / "static")), name="static")

    @app.exception_handler(PermissionError)
    async def local_storage_permission_error(_request: Request, _exc: PermissionError):
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "The local data folder is not writable. Close other app instances "
                    "and restart Network Assessor with normal user permissions."
                )
            },
        )

    @app.exception_handler(DocumentTooLarge)
    async def result_size_error(_request: Request, _exc: DocumentTooLarge):
        return JSONResponse(
            status_code=413,
            content={
                "detail": (
                    "This update exceeds the local report size limit. The previous "
                    "saved report is still available."
                )
            },
        )

    @app.get("/")
    async def home(request: Request):
        return templates.TemplateResponse(request=request, name="dashboard.html", context={})

    @app.get("/settings")
    async def settings_page(request: Request):
        return templates.TemplateResponse(request=request, name="settings.html", context={})

    @app.get("/history")
    async def history_page(request: Request):
        return templates.TemplateResponse(request=request, name="history.html", context={})

    @app.get("/scans/{scan_id}")
    async def scan_page(request: Request, scan_id: str):
        return templates.TemplateResponse(
            request=request, name="scan.html", context={"scan_id": scan_id}
        )

    app.include_router(session_api.router)
    app.include_router(scans_api.router)
    app.include_router(settings_api.router)
    app.include_router(demo_api.router)

    return app
