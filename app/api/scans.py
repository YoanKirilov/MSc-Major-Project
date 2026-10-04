from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import require_session
from app.config import (
    detect_private_network,
    mdns_interface_message,
    network_warning,
    nmap_interface_diagnostic,
    nmap_interface_ipv4,
    nmap_preflight,
    resolve_allowed_network,
    resolve_nmap_path,
)
from app.explanations.presentation import plain_finding, plain_report
from app.explanations.service import PROMPT_VERSION
from app.risk.catalogue import RULESET_VERSION
from app.risk.guidance import guidance_status
from app.scanner.commands import DEEP_PROFILE, DEEP_UDP_PORTS, PORTS, PROFILE_ID, UDP_PORTS
from app.scanner.cve import service_cpe
from app.scanner.mdns import mdns_available
from app.schemas.api import RefreshGuidanceRequest, ScanCreateRequest
from app.schemas.scan import ScanDocument
from app.security.scope import validate_target
from app.storage.nicknames import NicknameStore, NicknameUpdate

router = APIRouter(prefix="/api")


@router.put("/live-scans/{scan_id}/devices/{device_id}/nickname")
async def set_nickname(request: Request, scan_id: str, device_id: str, body: NicknameUpdate):
    require_session(request, csrf=True)
    try:
        document = await request.app.state.store.load_scan(scan_id)
        if document.source != "live" or document.phase != "finished":
            raise ValueError("Wait for the scan to finish before assigning a nickname")
        revision = await NicknameStore(request.app.state.store).update(document, device_id, body)
        return {"nickname_revision": revision}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Report or device not found") from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409, detail="Reload the report and check the nickname"
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503, detail="Nicknames are busy; try again shortly"
        ) from exc


@router.get("/scans")
async def list_scans(request: Request, source: str | None = None, offset: int = 0, limit: int = 20):
    require_session(request)
    if offset < 0 or not 1 <= limit <= 50:
        raise HTTPException(status_code=422, detail="Invalid history page")
    return await request.app.state.store.list_scans(source=source, offset=offset, limit=limit)


@router.get("/scans/{scan_id}")
async def get_scan(request: Request, scan_id: str):
    require_session(request)
    try:
        document = await request.app.state.store.load_scan(scan_id)
    except (FileNotFoundError, ValueError) as exc:
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


@router.post("/scans", status_code=202)
async def create_scan(request: Request, body: ScanCreateRequest):
    require_session(request, csrf=True)
    return await _create_validated_live_scan(request, body)


@router.post("/live-scans", status_code=202)
async def create_live_scan(request: Request, body: ScanCreateRequest):
    require_session(request, csrf=True)
    return await _create_validated_live_scan(request, body)


async def _create_validated_live_scan(
    request: Request, body: ScanCreateRequest, retry_of: str | None = None
):
    if not body.authorised:
        raise HTTPException(status_code=422, detail="Authorisation is required")
    if not await asyncio.to_thread(request.app.state.store.storage_writable):
        raise HTTPException(status_code=503, detail="The local data folder is not writable.")
    scanner_available, scanner_version = await asyncio.to_thread(
        nmap_preflight, request.app.state.config
    )
    nmap_path = resolve_nmap_path(request.app.state.config)
    if not scanner_available or not nmap_path:
        raise HTTPException(status_code=503, detail="Nmap is not installed or configured.")
    # Pick up a newly installed Nmap without retaining the startup fallback path.
    request.app.state.supervisor.nmap_path = nmap_path
    if body.mode not in {"discover", "known_hosts"}:
        raise HTTPException(status_code=422, detail="Unsupported scan mode")
    if body.profile not in {"light", DEEP_PROFILE}:
        raise HTTPException(status_code=422, detail="Unsupported scan profile")
    if body.profile == DEEP_PROFILE and body.mode != "known_hosts":
        raise HTTPException(status_code=422, detail="Deep scans require an explicit known host")
    if body.profile == DEEP_PROFILE and len(body.hosts) != 1:
        raise HTTPException(status_code=422, detail="Deep scans require exactly one host")
    settings = await request.app.state.store.load_settings()
    detected = await asyncio.to_thread(detect_private_network)
    scope = settings.allowed_network or resolve_allowed_network(request.app.state.config, detected)
    if body.confirmed_scope is not None and body.confirmed_scope != scope:
        raise HTTPException(
            status_code=409,
            detail=(
                "The network range changed since this page loaded. "
                "Reload and confirm the current network before scanning."
            ),
        )
    if scope and detected and network_warning(scope, detected):
        bound = (
            await asyncio.to_thread(
                nmap_interface_ipv4, request.app.state.config, scope, settings.interface
            )
            if settings.interface
            else None
        )
        if not bound:
            raise HTTPException(status_code=409, detail=network_warning(scope, detected))
    target_cidr = body.cidr or scope if body.mode == "discover" else body.cidr
    try:
        validated = validate_target(
            {
                "mode": body.mode,
                "cidr": target_cidr,
                "hosts": body.hosts,
                "authorised": body.authorised,
            },
            {"allowed_network": scope, "profile_id": PROFILE_ID},
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    from app.scanner.network import connection_snapshot

    context = await asyncio.to_thread(
        connection_snapshot, request.app.state.config, scope, settings.interface
    )
    if context is None:
        raise HTTPException(
            409,
            "The current network connection could not be verified. "
            "Check Network range and Interface in Settings before scanning.",
        )
    ai_available = await request.app.state.explanations.provider_available()
    mdns_interface_ip = None
    mdns_warning = None
    if settings.mdns_enabled:
        if not mdns_available():
            mdns_warning = (
                "Additional device-name discovery is not installed. "
                "The authorised Nmap checks will still run."
            )
        else:
            mdns_interface_ip = await asyncio.to_thread(
                nmap_interface_ipv4, request.app.state.config, scope, settings.interface
            )
        if mdns_interface_ip is None and mdns_warning is None:
            diagnostic = await asyncio.to_thread(
                nmap_interface_diagnostic, request.app.state.config, scope, settings.interface
            )
            mdns_warning = mdns_interface_message(diagnostic["reason"], scope, detected)
    scan_id = str(uuid4())
    targets = [
        {"ip": host, "discovery_status": "not_run", "service_status": "pending"}
        for host in validated.candidates
    ]
    document = ScanDocument(
        scan_id=scan_id,
        source="live",
        target={"mode": validated.mode, "cidr": validated.cidr, "hosts": list(validated.hosts)},
        policy={
            "allowed_network": scope,
            "network_context": context,
            "profile_id": PROFILE_ID if body.profile == "light" else DEEP_PROFILE,
            "profile": body.profile,
            "tcp_ports": list(PORTS) if body.profile == "light" else ["all-tcp"],
            "udp_ports": list(UDP_PORTS) if body.profile == "light" else list(DEEP_UDP_PORTS),
            "interface": settings.interface or context.get("interface"),
            "retain_raw_xml": settings.retain_raw_xml,
            "mdns_enabled": bool(mdns_interface_ip),
            "mdns_interface_ip": mdns_interface_ip,
            "ai_enabled": True,
            "pihole_enabled": settings.pihole_enabled,
            "extra_details_enabled": True,
            "extra_details_budget_seconds": 30,
            "extra_details_version": "1.0.1",
            "retry_of": retry_of,
        },
        coverage={"candidate_count": len(validated.candidates), "targets": targets},
        versions={
            "app": "0.1.0",
            "rules": RULESET_VERSION,
            "profiling": "1.1.1",
            "prompt": PROMPT_VERSION,
            "nmap": scanner_version,
        },
        warnings=[]
        if ai_available
        else [
            {
                "code": "AI_PREFLIGHT_UNAVAILABLE",
                "message": (
                    "Ollama was unavailable before scanning. Report preparation will "
                    "be attempted after the observations are saved."
                ),
            }
        ],
    )
    if mdns_warning:
        document.warnings.append({"code": "MDNS_UNAVAILABLE", "message": mdns_warning})
    await request.app.state.store.create_scan(document)
    try:
        await request.app.state.supervisor.start(scan_id)
    except RuntimeError as exc:
        await request.app.state.store.delete_scan(scan_id)
        if str(exc) == "SCAN_CAPACITY":
            limit = request.app.state.supervisor.max_concurrent_scans
            raise HTTPException(
                status_code=429,
                detail=f"Scan capacity reached ({limit} running scans).",
            ) from exc
        raise
    return {"scan_id": scan_id, "state": "queued", "status_url": f"/api/live-scans/{scan_id}"}


@router.get("/live-scans/{scan_id}")
async def get_live_scan(request: Request, scan_id: str):
    require_session(request)
    try:
        document = await request.app.state.store.load_scan(scan_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Live scan result not found") from exc
    if document.source != "live":
        raise HTTPException(status_code=404, detail="Live scan result not found")
    payload = document.model_dump(mode="json")
    # Presentation is editorial and never saved over scan facts.
    for service, presented in zip(document.services, payload["services"], strict=True):
        presented["cve_lookup_available"] = service_cpe(service) is not None
    payload["plain_guidance"] = {item.finding_id: plain_finding(item) for item in document.findings}
    payload["plain_overview"] = plain_report(document)
    payload["guidance_status"] = {**guidance_status(document), "ai_prompt_version": PROMPT_VERSION}
    try:
        revision, names = await NicknameStore(request.app.state.store).view(document)
        payload["nickname_revision"] = revision
        payload["user_nicknames"] = names
    except (OSError, ValueError):
        payload["nickname_error"] = "Saved nicknames could not be read; scan evidence is unchanged."
    return payload


@router.get("/live-scans/{scan_id}/progress")
async def get_live_progress(request: Request, scan_id: str):
    require_session(request)
    try:
        progress = await request.app.state.store.load_progress(scan_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Live scan result not found") from exc
    if progress["source"] != "live":
        raise HTTPException(status_code=404, detail="Live scan result not found")
    return progress


@router.post("/live-scans/{scan_id}/retry-hosts", status_code=202)
async def retry_unfinished_hosts(request: Request, scan_id: str, body: RefreshGuidanceRequest):
    require_session(request, csrf=True)
    try:
        document = await request.app.state.store.load_scan(scan_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Scan not found") from exc
    if (
        document.source != "live"
        or document.phase != "finished"
        or document.revision != body.expected_revision
    ):
        raise HTTPException(
            status_code=409,
            detail="The report changed or is still running. Reload before retrying.",
        )
    hosts = [
        target.ip
        for target in document.coverage.targets
        if target.service_status in {"failed", "timed_out", "cancelled", "pending", "running"}
        and (document.target.get("mode") == "known_hosts" or target.discovery_status == "observed")
    ]
    if not hosts:
        raise HTTPException(
            status_code=409, detail="There are no unfinished device checks to retry."
        )
    return await _create_validated_live_scan(
        request,
        ScanCreateRequest(
            mode="known_hosts",
            hosts=hosts,
            profile=document.policy.get("profile", "light"),
            authorised=True,
        ),
        retry_of=scan_id,
    )


@router.get("/live-scans/{scan_id}/guidance/{name}")
async def get_archived_guidance(request: Request, scan_id: str, name: str):
    require_session(request)
    try:
        return await request.app.state.store.load_guidance_archive(scan_id, name)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Saved guidance not found") from exc


@router.post("/live-scans/{scan_id}/refresh-guidance")
async def refresh_saved_guidance(request: Request, scan_id: str, body: RefreshGuidanceRequest):
    require_session(request, csrf=True)
    try:
        document = await request.app.state.store.load_scan(scan_id)
        if document.source != "live":
            raise FileNotFoundError(scan_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Live scan result not found") from exc
    try:
        updated = await request.app.state.supervisor.refresh_guidance(
            scan_id, body.expected_revision
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail="The report changed or is still busy. Reload it before refreshing guidance.",
        ) from exc
    return {"scan_id": scan_id, "revision": updated.revision}


@router.post("/live-scans/{scan_id}/explanations", status_code=202)
async def simplify_saved_scan(request: Request, scan_id: str):
    require_session(request, csrf=True)
    try:
        document = await request.app.state.store.load_scan(scan_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Live scan not found") from exc
    if document.source != "live":
        raise HTTPException(status_code=404, detail="Live scan not found")
    if not await request.app.state.explanations.provider_available():
        raise HTTPException(status_code=503, detail="The local Ollama model is not available.")
    try:
        await request.app.state.supervisor.request_explanations(scan_id)
    except RuntimeError as exc:
        if str(exc) in {"SCAN_BUSY", "SCAN_NOT_READY"}:
            raise HTTPException(
                status_code=409, detail="This report is not ready for AI wording."
            ) from exc
        if str(exc) in {"AI_DISABLED", "AI_NOT_CONFIGURED"}:
            raise HTTPException(status_code=503, detail="Local AI wording is unavailable.") from exc
        raise
    return {"scan_id": scan_id, "state": "analysing", "status_url": f"/api/live-scans/{scan_id}"}


@router.delete("/live-scans/{scan_id}", status_code=202)
async def cancel_live_scan(request: Request, scan_id: str):
    require_session(request, csrf=True)
    try:
        document = await request.app.state.store.load_scan(scan_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Live scan not found") from exc
    if document.source != "live":
        raise HTTPException(status_code=404, detail="Live scan not found")
    if not await request.app.state.supervisor.cancel(scan_id):
        raise HTTPException(status_code=409, detail="Scan is not running")
    return {"scan_id": scan_id, "state": "cancelling"}
