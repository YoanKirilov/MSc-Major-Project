"""Authenticated browsing and user annotations, separate from scan execution."""

import asyncio
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.dependencies import require_session
from app.config import (
    detect_private_network,
    network_warning,
    nmap_interface_ipv4,
    resolve_allowed_network,
)
from app.scanner.name_refresh import lookup_names
from app.schemas.common import StrictModel
from app.schemas.scan import ScanState
from app.security.scope import validate_target
from app.storage.annotations import ActionCheckUpdate, AnnotationStore, TitleUpdate
from app.storage.library import search_reports
from app.storage.nicknames import NicknameStore

router = APIRouter(prefix="/api")


async def note_operation(operation):
    """Consistent failure boundary for notes; never reset notes or retry writes."""
    try:
        return await operation
    except OSError as exc:
        raise HTTPException(
            503,
            "Saved report notes are unavailable. Original scan results are preserved; "
            "reload before editing.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            409,
            "Report notes changed, are unreadable, or this action is unavailable; "
            "reload before saving.",
        ) from exc


class NameRefreshRequest(StrictModel):
    authorised: bool = False


@router.post("/live-scans/{scan_id}/devices/{device_id}/refresh-name")
async def refresh_name(request: Request, scan_id: str, device_id: str, body: NameRefreshRequest):
    require_session(request, csrf=True)
    if not body.authorised:
        raise HTTPException(422, "Confirm permission for a name lookup on this address")
    doc = await live_document(request, scan_id)
    device = next((item for item in doc.devices if item.device_id == device_id), None)
    if device is None:
        raise HTTPException(404, "Device not found")
    if doc.phase != "finished":
        raise HTTPException(409, "Wait for the scan to finish before refreshing identification")
    settings = await request.app.state.store.load_settings()
    config = request.app.state.config
    detected = await asyncio.to_thread(detect_private_network)
    scope = settings.allowed_network or resolve_allowed_network(config, detected)
    if not scope:
        raise HTTPException(409, "Configure the authorised network before an identification lookup")
    bound = None
    if settings.interface or settings.mdns_enabled:
        bound = await asyncio.to_thread(nmap_interface_ipv4, config, scope, settings.interface)
    if network_warning(scope, detected) and not bound:
        raise HTTPException(
            409, "Confirm the current authorised network and interface in Settings first"
        )
    try:
        validate_target(
            {"mode": "known_hosts", "hosts": [device.ip], "authorised": True},
            {"allowed_network": scope},
        )
    except ValueError as exc:
        raise HTTPException(
            422, "This saved address is outside the current authorised scope"
        ) from exc
    lock = request.app.state.name_refresh_lock
    await note_operation(AnnotationStore(request.app.state.store).load(scan_id))
    if lock.locked():
        raise HTTPException(429, "Another identification lookup is running; try again shortly")
    async with lock:
        try:
            async with asyncio.timeout(10):
                refresh = await lookup_names(
                    device, scope, bound if settings.mdns_enabled else None
                )
        except TimeoutError as exc:
            raise HTTPException(
                503, "Identification timed out; original scan evidence is unchanged"
            ) from exc
        return await note_operation(
            AnnotationStore(request.app.state.store).update(scan_id, refresh=refresh)
        )


async def live_document(request, scan_id):
    try:
        doc = await request.app.state.store.load_scan(scan_id)
        if doc.source != "live":
            raise ValueError("Not live")
        return doc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(404, "Live report not found") from exc


@router.get("/reports")
async def reports(
    request: Request,
    q: str = Query("", max_length=120),
    profile: Literal["light", "deep-tcp-v1"] | None = None,
    state: ScanState | None = None,
    after: date | None = None,
    before: date | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
):
    require_session(request)
    if after and before and after > before:
        raise HTTPException(422, "Start date must not be after end date")
    return await asyncio.to_thread(
        search_reports,
        request.app.state.store,
        q=q,
        profile=profile,
        state=state,
        after=after,
        before=before,
        offset=offset,
        limit=limit,
    )


@router.get("/recent-devices")
async def recent_devices(request: Request):
    require_session(request)
    settings = await request.app.state.store.load_settings()
    detected = await asyncio.to_thread(detect_private_network)
    scope = settings.allowed_network or resolve_allowed_network(request.app.state.config, detected)
    if not scope:
        return {"items": [], "total": 0, "days": 7}
    return await asyncio.to_thread(
        search_reports, request.app.state.store, profile="light", scope=scope, recent_devices=True
    )


@router.get("/running-scans")
async def running_scans(request: Request):
    require_session(request)
    items = []
    for scan_id in request.app.state.supervisor.active_scan_ids:
        try:
            doc = await request.app.state.store.load_scan(scan_id)
            items.append(
                {
                    "scan_id": scan_id,
                    "profile": doc.policy.get("profile"),
                    "target": doc.target,
                    "started_at": doc.started_at or doc.created_at,
                    "phase": doc.phase,
                    "analysis_progress": doc.analysis_progress,
                    "completed": doc.coverage.service_completed_count,
                    "total": doc.coverage.discovered_count
                    if doc.target.get("mode") == "discover"
                    else doc.coverage.candidate_count,
                }
            )
        except (OSError, ValueError):
            items.append({"scan_id": scan_id, "phase": "unavailable"})
    return {"items": items}


@router.get("/storage-usage")
async def storage_usage(request: Request):
    require_session(request)
    from app.storage.backup import storage_usage as measure

    try:
        return await asyncio.to_thread(measure, request.app.state.store.data_root)
    except (OSError, ValueError) as exc:
        raise HTTPException(
            503, "Storage usage could not be measured; saved reports are unchanged"
        ) from exc


@router.get("/live-scans/{scan_id}/annotations")
async def annotations(request: Request, scan_id: str):
    require_session(request)
    await live_document(request, scan_id)
    return await note_operation(AnnotationStore(request.app.state.store).load(scan_id))


@router.put("/live-scans/{scan_id}/title")
async def title(request: Request, scan_id: str, body: TitleUpdate):
    require_session(request, csrf=True)
    await live_document(request, scan_id)
    return await note_operation(
        AnnotationStore(request.app.state.store).update(scan_id, title=body)
    )


@router.get("/live-scans/{scan_id}/nicknames")
async def nicknames(request: Request, scan_id: str, revision: int | None = Query(None, ge=1)):
    require_session(request)
    doc = await live_document(request, scan_id)
    return await NicknameStore(request.app.state.store).snapshot(doc, revision)


@router.put("/live-scans/{scan_id}/action-checks")
async def action_checks(request: Request, scan_id: str, body: ActionCheckUpdate):
    require_session(request, csrf=True)
    await live_document(request, scan_id)
    return await note_operation(
        AnnotationStore(request.app.state.store).update(scan_id, action_check=body)
    )
