"""Explicitly labelled demonstration endpoints; never perform network scans."""

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import require_session

router = APIRouter(prefix="/api")


@router.get("/demo-findings")
async def demo_findings(request: Request):
    return request.app.state.demo_data.load()


@router.post("/demo-runs", status_code=201)
async def create_demo_run(request: Request):
    require_session(request, csrf=True)
    run = await asyncio.to_thread(request.app.state.demo_runs.create)
    return {"run_id": run["run_id"], "source": "demo", "state": "completed"}


@router.get("/demo-runs/{run_id}")
async def get_demo_run(request: Request, run_id: str):
    require_session(request)
    try:
        return await asyncio.to_thread(request.app.state.demo_runs.load, run_id)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Demo run not found") from exc
