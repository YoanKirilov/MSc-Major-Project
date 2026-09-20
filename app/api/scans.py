from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.schemas.api import DemoScanRequest, ScanCreateRequest
from app.schemas.scan import ScanDocument

router = APIRouter(prefix="/api")


def require_session(request: Request, csrf: bool = False):
    request.app.state.session_manager.authenticate(request, require_csrf=csrf)


@router.get("/scans")
async def list_scans(request: Request, source: str | None = None, offset: int = 0, limit: int = 20):
    require_session(request)
    return await request.app.state.store.list_scans(source=source, offset=offset, limit=min(limit, 50))


@router.get("/scans/{scan_id}")
async def get_scan(request: Request, scan_id: str):
    require_session(request)
    try:
        document = await request.app.state.store.load_scan(scan_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Scan not found") from exc
    return {
        "scan_id": document.scan_id,
        "revision": document.revision,
        "state": document.state,
        "phase": document.phase,
        "source": document.source,
        "target": document.target,
        "policy": document.policy,
        "coverage": document.coverage.model_dump(mode="json"),
        "warnings": document.warnings,
        "errors": document.errors,
        "created_at": document.created_at,
        "started_at": document.started_at,
        "finished_at": document.finished_at,
        "finding_count": len(document.findings),
        "device_count": len(document.devices),
    }


@router.post("/demo-scans", status_code=201)
async def create_demo_scan(request: Request, body: DemoScanRequest):
    require_session(request, csrf=True)
    scan_id = str(uuid4())
    document = ScanDocument(
        scan_id=scan_id,
        source="demo",
        state="completed",
        phase="finished",
        target={"mode": "demo", "cidr": None, "hosts": []},
        finished_at="2026-09-20T00:00:00Z",
    )
    await request.app.state.store.create_scan(document)
    return {"scan_id": scan_id, "state": "completed", "status_url": f"/scans/{scan_id}"}


@router.post("/scans", status_code=202)
async def create_scan(request: Request, body: ScanCreateRequest):
    require_session(request, csrf=True)
    if not body.authorised:
        raise HTTPException(status_code=422, detail="Authorisation is required")
    if body.mode not in {"discover", "known_hosts"}:
        raise HTTPException(status_code=422, detail="Unsupported scan mode")
    scan_id = str(uuid4())
    target = {"mode": body.mode, "cidr": body.cidr, "hosts": body.hosts}
    document = ScanDocument(scan_id=scan_id, target=target, source="live")
    await request.app.state.store.create_scan(document)
    try:
        await request.app.state.supervisor.start(scan_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail="Another scan is already active") from exc
    return {"scan_id": scan_id, "state": "queued", "status_url": f"/api/scans/{scan_id}"}
