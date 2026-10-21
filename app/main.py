from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from filelock import FileLock, Timeout

from .api import cves as cves_api
from .api import demo as demo_api
from .api import devices as devices_api
from .api import library as library_api
from .api import report_export as report_export_api
from .api import scans as scans_api
from .api import session as session_api
from .api import settings as settings_api
from .build_info import RUNNING_BUILD
from .config import load_config, resolve_nmap_path
from .demo.adapter import DemoFindingsAdapter
from .demo.runs import DemoRunStore
from .explanations import ExplanationService, OllamaExplanationProvider
from .explanations.runtime import OllamaRuntime
from .jobs.start_requests import StartRequests
from .jobs.supervisor import ScanSupervisor
from .runtime_diagnostics import observe_asyncio_errors
from .scanner.cve import NvdClient
from .scanner.pihole import PiholeClient
from .scanner.reverse_dns import ReverseDnsResolver
from .security.headers import LOCAL_RESPONSE_HEADERS, LocalResponseHeaders
from .security.session import SessionManager
from .static_assets import AppStaticFiles
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
        with observe_asyncio_errors(asyncio.get_running_loop()) as diagnostics:
            app.state.asyncio_diagnostics = diagnostics
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
    app.state.running_build = dict(RUNNING_BUILD)
    app.state.runtime_status_lock = asyncio.Lock()
    app.state.name_refresh_lock = asyncio.Lock()
    app.state.cve_lookup_lock = asyncio.Lock()
    app.state.nvd = NvdClient()
    app.state.runtime_status_cache = None
    app.state.store = JsonStore(data_dir)
    app.state.name_resolver = ReverseDnsResolver()
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
        app_config=config,
        name_resolver=app.state.name_resolver,
    )
    await app.state.supervisor.reconcile_incomplete()
    app.state.start_requests = StartRequests(app.state.store, app.state.supervisor)
    app.state.ollama_runtime = None
    if explanation_provider is not None and config.ai_autostart:
        runtime = OllamaRuntime(explanation_provider)
        explanation_provider.runtime = runtime
        app.state.ollama_runtime = runtime
        runtime.start()
    try:
        yield
    finally:
        try:
            await app.state.start_requests.shutdown()
            await app.state.supervisor.shutdown()
        finally:
            if app.state.ollama_runtime is not None:
                await app.state.ollama_runtime.close()


def create_app(*, session_manager: SessionManager | None = None) -> FastAPI:
    # The home-user UI is entirely same-origin. FastAPI's optional Swagger/ReDoc
    # pages use external scripts and inline bootstraps incompatible with that CSP;
    # retain the machine-readable schema rather than serving broken CDN-based UIs.
    app = FastAPI(title="Network Assessor", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.initial_session_manager = session_manager
    app.state.response_factory = JSONResponse
    app_root = Path(__file__).resolve().parent
    templates = Jinja2Templates(directory=str(app_root / "templates"))
    app.state.templates = templates
    app.mount("/static", AppStaticFiles(directory=str(app_root / "static")), name="static")

    app.add_middleware(LocalResponseHeaders)

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, _exc: Exception):
        # Starlette's outer ServerErrorMiddleware handles unexpected errors outside
        # user middleware. Keep those responses protected too, without leaking
        # exception details or suppressing the server's exception logging.
        return JSONResponse(
            status_code=500,
            headers=LOCAL_RESPONSE_HEADERS,
            content={
                "detail": "The local app encountered an unexpected error. Reload to reconnect."
            },
        )

    @app.exception_handler(Timeout)
    async def local_storage_busy(_request: Request, _exc: Timeout):
        return JSONResponse(
            status_code=503,
            headers={"Retry-After": "1"},
            content={
                "detail": (
                    "Saved results or settings are busy. Try again shortly; "
                    "existing data is unchanged."
                )
            },
        )

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

    @app.get("/light")
    async def light_page(request: Request):
        return templates.TemplateResponse(
            request=request, name="dashboard.html", context={"scan_page": "light"}
        )

    @app.get("/deep")
    async def deep_page(request: Request):
        return templates.TemplateResponse(
            request=request, name="dashboard.html", context={"scan_page": "deep"}
        )

    @app.get("/settings")
    async def settings_page(request: Request):
        return templates.TemplateResponse(request=request, name="settings.html", context={})

    @app.get("/history")
    async def history_page(request: Request):
        return templates.TemplateResponse(request=request, name="history.html", context={})

    @app.get("/devices")
    async def devices_page(request: Request):
        return templates.TemplateResponse(request=request, name="devices.html", context={})

    @app.get("/scans/{scan_id}")
    async def scan_page(request: Request, scan_id: str):
        return templates.TemplateResponse(
            request=request, name="scan.html", context={"scan_id": scan_id}
        )

    app.include_router(session_api.router)
    app.include_router(scans_api.router)
    app.include_router(library_api.router)
    app.include_router(report_export_api.router)
    app.include_router(cves_api.router)
    app.include_router(settings_api.router)
    app.include_router(demo_api.router)
    app.include_router(devices_api.router)

    return app
