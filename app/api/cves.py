"""User-requested public CVE research on saved evidence, never an active device scan."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import require_session
from app.api.library import live_document, note_operation
from app.explanations.cve import explain_cves
from app.scanner.cve import NvdBusy, service_cpe
from app.schemas.common import utc_now
from app.storage.annotations import AnnotationStore

router = APIRouter(prefix="/api")


@router.post("/live-scans/{scan_id}/services/{service_id}/cves")
async def lookup_cves(request: Request, scan_id: str, service_id: str):
    require_session(request, csrf=True)
    document = await live_document(request, scan_id)
    if document.phase != "finished":
        raise HTTPException(409, "Wait for the report to finish before checking CVEs")
    service = next((item for item in document.services if item.service_id == service_id), None)
    if service is None:
        raise HTTPException(404, "Saved service not found")
    lock = request.app.state.cve_lookup_lock
    if lock.locked():
        raise HTTPException(429, "Another CVE lookup is running. Try again shortly.")
    async with lock:
        store = AnnotationStore(request.app.state.store)
        annotations = await note_operation(store.load(scan_id))
        cached = next((r for r in annotations.cve_lookups if r.service_id == service_id), None)
        if (
            cached
            and cached.query == service_cpe(service)
            and cached.status in {"candidates", "no_matches"}
            and (cached.status == "candidates" or cached.resolution is not None)
        ):
            try:
                age = (utc_now() - datetime.fromisoformat(cached.checked_at)).total_seconds()
            except (ValueError, TypeError):
                age = -1
            if 0 <= age < 86400:
                if cached.ai_source == "fixed":
                    cached = await explain_cves(
                        cached,
                        request.app.state.explanations.provider,
                        busy=bool(request.app.state.supervisor.active_scan_ids),
                    )
                    annotations = await note_operation(store.update(scan_id, cve=cached))
                return {
                    "lookup": cached,
                    "revision": annotations.revision,
                    "annotations": annotations,
                    "cached": True,
                }
        if cached is None and len(annotations.cve_lookups) >= 128:
            raise HTTPException(409, "This report has reached its limit of 128 saved CVE lookups")
        try:
            result = await request.app.state.nvd.lookup(service)
        except NvdBusy as exc:
            raise HTTPException(
                429,
                "The CVE database needs a short pause. Try again in 30 seconds.",
                headers={"Retry-After": "30"},
            ) from exc
        result = await explain_cves(
            result,
            request.app.state.explanations.provider,
            busy=bool(request.app.state.supervisor.active_scan_ids),
        )
        updated = await note_operation(store.update(scan_id, cve=result))
        return {
            "lookup": result,
            "revision": updated.revision,
            "annotations": updated,
            "cached": False,
        }
