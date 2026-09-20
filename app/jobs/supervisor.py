from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timezone
from typing import Any

from app.risk.engine import evaluate_device
from app.scanner.commands import host_command
from app.scanner.parser import parse_host
from app.scanner.runner import ProcessResult, run_process
from app.storage.json_store import JsonStore


class ScanSupervisor:
    def __init__(self, store: JsonStore, nmap_path: str = "nmap", process_runner=run_process):
        self.store = store
        self.nmap_path = nmap_path
        self.process_runner = process_runner
        self._tasks: dict[str, asyncio.Task] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._admission = asyncio.Lock()

    def is_active(self, scan_id: str | None = None) -> bool:
        if scan_id is not None:
            task = self._tasks.get(scan_id)
            return task is not None and not task.done()
        return any(not task.done() for task in self._tasks.values())

    async def start(self, scan_id: str) -> None:
        async with self._admission:
            if self.is_active():
                raise RuntimeError("SCAN_BUSY")
            cancel_event = asyncio.Event()
            self._cancel_events[scan_id] = cancel_event
            self._tasks[scan_id] = asyncio.create_task(self._run(scan_id, cancel_event))

    async def cancel(self, scan_id: str) -> bool:
        event = self._cancel_events.get(scan_id)
        if event is None:
            return False
        event.set()
        return True

    async def shutdown(self) -> None:
        for event in self._cancel_events.values():
            event.set()
        tasks = list(self._tasks.values())
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        self._cancel_events.clear()

    async def _checkpoint(self, scan_id: str, mutate: Callable[[Any], Any]) -> None:
        await self.store.update_scan(scan_id, mutate)

    async def _run(self, scan_id: str, cancel_event: asyncio.Event) -> None:
        try:
            document = await self.store.load_scan(scan_id)
            await self._checkpoint(scan_id, lambda current: current.model_copy(update={"state": "running", "phase": "service_scan", "started_at": current.created_at}))
            target_hosts = tuple(document.target.get("hosts", []))
            for ip in target_hosts:
                if cancel_event.is_set():
                    break
                result: ProcessResult = await self.process_runner(host_command(self.nmap_path, ip), 30, cancel_event)
                if result.cancelled:
                    break
                if result.timed_out or result.overflow or result.returncode != 0:
                    await self._checkpoint(scan_id, lambda current, ip=ip: current.model_copy(update={
                        "errors": [*current.errors, {"code": "HOST_SCAN_FAILED", "message": "Host scan did not complete.", "device_id": None}],
                    }))
                    continue
                device, services = parse_host(result.stdout, ip, scan_id, "known_host")
                device.profile = device.profile.model_validate({"category": "unknown", "confidence": "low", "hints": [], "conflict": False})
                findings = evaluate_device(device, services)
                def commit(current, device=device, services=services, findings=findings, ip=ip):
                    coverage = current.coverage.model_copy(deep=True)
                    coverage.service_attempted_count += 1
                    coverage.service_completed_count += 1
                    for target in coverage.targets:
                        if target.ip == ip:
                            target.service_status = "completed"
                    return current.model_copy(update={
                        "devices": [*current.devices, device],
                        "services": [*current.services, *services],
                        "findings": [*current.findings, *findings],
                        "coverage": coverage,
                    })
                await self._checkpoint(scan_id, commit)
            final_state = "cancelled" if cancel_event.is_set() else "completed"
            await self._checkpoint(scan_id, lambda current: current.model_copy(update={"state": final_state, "phase": "finished", "finished_at": current.created_at}))
        except Exception as exc:
            await self._checkpoint(scan_id, lambda current: current.model_copy(update={
                "state": "failed" if not current.devices else "partial",
                "phase": "finished",
                "finished_at": current.created_at,
                "errors": [*current.errors, {"code": "SCAN_FAILED", "message": str(exc)[:200], "device_id": None}],
            }))
        finally:
            self._cancel_events.pop(scan_id, None)
            self._tasks.pop(scan_id, None)
