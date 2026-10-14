"""Authenticated saved device inventory and revision-protected household labels."""

import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.storage.device_inventory import (
    DEVICE_KEY_PATTERN,
    DeviceInventory,
    DeviceLabelUpdate,
    LabelCapacityExceeded,
    LabelRevisionConflict,
    LabelsUnavailable,
    UnknownDevice,
)

from .dependencies import require_session

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def list_devices(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
    search: str = Query("", max_length=120),
    view: Literal["all", "favourites", "not-recognised", "unfinished", "review"] = "all",
):
    require_session(request)
    try:
        return await asyncio.to_thread(
            DeviceInventory(request.app.state.store).list,
            offset=offset,
            limit=limit,
            search=search,
            view=view,
        )
    except LabelsUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.put("/{device_key}")
async def update_device(
    request: Request,
    body: DeviceLabelUpdate,
    device_key: str = Path(pattern=f"^{DEVICE_KEY_PATTERN}$"),
):
    require_session(request, csrf=True)
    try:
        return await asyncio.to_thread(
            DeviceInventory(request.app.state.store).update, device_key, body
        )
    except LabelRevisionConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except UnknownDevice as exc:
        raise HTTPException(404, str(exc)) from exc
    except (LabelsUnavailable, LabelCapacityExceeded) as exc:
        raise HTTPException(
            503, "Household labels could not be saved safely; existing labels are unchanged."
        ) from exc
