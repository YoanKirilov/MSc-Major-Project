"""Opt-in Light checks while the local app is open; no execution authority is restored."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import timedelta
from time import monotonic

from fastapi import HTTPException, Request

from app.config import detect_private_network, network_warning, resolve_allowed_network
from app.scanner.network import SnapshotUnavailable, connection_snapshot
from app.schemas.api import ScanCreateRequest
from app.schemas.common import iso_z, utc_now
from app.security.scope import validate_target
from app.storage.monitoring import (
    MonitoringCounts,
    MonitoringDocument,
    MonitoringRevisionConflict,
    MonitoringStore,
    MonitoringUnavailable,
    add_event,
)

POLL_SECONDS = 10
SUSPEND_GAP_SECONDS = 60
LOCAL_READ_TIMEOUT = 12
SCOPE_CACHE_SECONDS = 60
SUBMISSION_TIMEOUT = 45
SHUTDOWN_TIMEOUT = 15


class MonitoringService:
    def __init__(self, app, *, clock=monotonic, wall_clock=utc_now, submit=None):
        self.app = app
        self.store = MonitoringStore(app.state.store)
        self.clock = clock
        self.wall_clock = wall_clock
        self.submit = submit or self._submit
        self._lock = asyncio.Lock()
        self._scope_lock = asyncio.Lock()
        self._stop = asyncio.Event()
        self._task = None
        self._loaded = False
        self._writable_this_run = False
        self._available = True
        self._state = MonitoringDocument()
        self._guard_error = None
        self._approved_context = None
        self._approved_interface = None
        self._next_due = None
        self._last_tick = None
        self._scope_cache = None
        self._scope_checked = None
        self._closed = False

    async def _bounded(self, operation):
        async with asyncio.timeout(LOCAL_READ_TIMEOUT):
            return await operation

    def _time(self):
        return iso_z(self.wall_clock())

    def _next_time(self, seconds):
        return iso_z(self.wall_clock() + timedelta(seconds=seconds))

    def _change(self, document, **changes):
        return MonitoringDocument.model_validate({**document.model_dump(), **changes}, strict=True)

    async def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            self._state = await self._bounded(self.store.load())
        except (MonitoringUnavailable, OSError, TimeoutError):
            self._storage_failure()
            return
        if self._state.enabled:
            self._state = add_event(
                self._change(
                    self._state, enabled=False, next_check_at=None, pause_reason="restarted"
                ),
                "paused",
                "The app restarted. Periodic checks are paused; confirm permission and the "
                "current network before enabling them again.",
                occurred_at=self._time(),
            )

    def _storage_failure(self):
        self._available = False
        self._approved_context = None
        self._next_due = None
        self._guard_error = (
            "Periodic check settings could not be read or saved safely. Checks are paused; "
            "existing settings were not reset."
        )
        self._state = add_event(
            self._change(
                self._state, enabled=False, next_check_at=None, pause_reason="storage_unavailable"
            ),
            "paused",
            self._guard_error,
            occurred_at=self._time(),
        )

    async def _persist(self, document):
        try:
            self._state = await self._bounded(self.store.replace(document, self._state.revision))
        except (MonitoringUnavailable, MonitoringRevisionConflict, OSError, TimeoutError):
            self._storage_failure()
            raise

    async def _scope_info(self, *, force=False):
        async with self._scope_lock:
            now = self.clock()
            if (
                not force
                and self._scope_cache is not None
                and self._scope_checked is not None
                and 0 <= now - self._scope_checked < SCOPE_CACHE_SECONDS
            ):
                return self._scope_cache
            settings = await self._bounded(self.app.state.store.load_settings())
            detected = await self._bounded(asyncio.to_thread(detect_private_network))
            scope = settings.allowed_network or resolve_allowed_network(
                self.app.state.config, detected
            )
            if scope:
                validate_target(
                    {"mode": "discover", "cidr": scope, "authorised": True},
                    {"allowed_network": scope},
                )
            self._scope_cache = (settings, detected, scope)
            self._scope_checked = now
            return self._scope_cache

    async def _capture(self, scope, *, force=True):
        settings, detected, current_scope = await self._scope_info(force=force)
        if not current_scope or current_scope != scope:
            raise HTTPException(409, "The authorised network range changed; reload and confirm it")
        if detected is None and not settings.interface:
            raise SnapshotUnavailable("route_unavailable")
        if network_warning(scope, detected) and not settings.interface:
            raise HTTPException(
                409, "The current network could not be verified for periodic checks"
            )
        context = await self._bounded(
            asyncio.to_thread(
                connection_snapshot, self.app.state.config, scope, settings.interface, strict=True
            )
        )
        if not isinstance(context, dict) or not context:
            raise SnapshotUnavailable("snapshot_unavailable")
        return settings.interface, context

    async def status(self):
        async with self._lock:
            await self._ensure_loaded()
            if not self._available:
                try:
                    recovered = await self._bounded(self.store.load())
                except (MonitoringUnavailable, OSError, TimeoutError):
                    pass
                else:
                    self._state = self._change(
                        recovered,
                        enabled=False,
                        next_check_at=None,
                        pause_reason="storage_unavailable",
                    )
                    self._available = True
                    self._guard_error = (
                        "Periodic checks are paused after a settings read/save problem. "
                        "Confirm them before enabling again."
                    )
            state = self._state.model_dump(mode="json")
            available = self._available
            error = self._guard_error
        current_scope = None
        try:
            _, _, current_scope = await self._scope_info()
            if current_scope is None:
                error = error or "Choose a current authorised private network range in Settings."
        except (OSError, ValueError, TimeoutError):
            error = error or "The current authorised network range could not be read. Try again."
        state.update(
            revision=state["revision"] if available else None,
            available=available,
            current_scope=current_scope,
            configuration_error=error,
        )
        return state

    async def configure(self, body):
        async with self._lock:
            await self._ensure_loaded()
            if not self._available:
                raise HTTPException(503, self._guard_error)
            if body.expected_revision != self._state.revision:
                raise HTTPException(409, "Periodic check settings changed; reload before saving")
            context = None
            interface = None
            if body.enabled:
                if not body.authorised or not body.confirmed_scope:
                    raise HTTPException(422, "Confirm permission and the current network range")
                try:
                    interface, context = await self._capture(body.confirmed_scope)
                except HTTPException:
                    raise
                except (OSError, ValueError, SnapshotUnavailable, TimeoutError) as exc:
                    raise HTTPException(
                        409, "The current network connection could not be verified"
                    ) from exc
                changed = self._change(
                    self._state,
                    enabled=True,
                    scope=body.confirmed_scope,
                    interval_minutes=body.interval_minutes,
                    pause_reason=None,
                    next_check_at=self._next_time(body.interval_minutes * 60),
                )
                changed = add_event(
                    changed,
                    "enabled",
                    f"Periodic Light checks enabled every {body.interval_minutes} minutes while "
                    "this app is open. The first check starts after this interval.",
                    occurred_at=self._time(),
                )
            else:
                changed = add_event(
                    self._change(
                        self._state,
                        enabled=False,
                        next_check_at=None,
                        interval_minutes=body.interval_minutes,
                        pause_reason=None,
                    ),
                    "disabled",
                    "Periodic checks switched off. An already running check can finish.",
                    occurred_at=self._time(),
                )
            try:
                await self._persist(changed)
            except MonitoringRevisionConflict as exc:
                raise HTTPException(
                    409, "Periodic check settings changed; reload before saving"
                ) from exc
            except (MonitoringUnavailable, OSError, TimeoutError) as exc:
                raise HTTPException(
                    503, "Periodic check settings could not be saved safely"
                ) from exc
            self._approved_context = deepcopy(context)
            self._writable_this_run = True
            self._approved_interface = interface
            self._next_due = self.clock() + body.interval_minutes * 60 if body.enabled else None
            self._last_tick = self.clock()
            self._guard_error = None
        return await self.status()

    async def _pause(self, reason, message):
        self._approved_context = None
        self._next_due = None
        self._guard_error = message
        changed = add_event(
            self._change(self._state, enabled=False, next_check_at=None, pause_reason=reason),
            "paused",
            message,
            occurred_at=self._time(),
        )
        await self._persist(changed)

    async def _defer(self, now, message):
        interval = self._state.interval_minutes * 60
        self._next_due = now + interval
        changed = add_event(
            self._change(self._state, next_check_at=self._next_time(interval)),
            "deferred",
            message,
            occurred_at=self._time(),
        )
        await self._persist(changed)

    async def _record_result(self):
        if (
            not self._writable_this_run
            or not self._state.last_scan_id
            or self._state.last_outcome != "queued"
        ):
            return
        try:
            progress = await self._bounded(
                self.app.state.store.load_progress(self._state.last_scan_id)
            )
            if progress.get("phase") != "finished":
                return
            document = await self._bounded(self.app.state.store.load_scan(self._state.last_scan_id))
            if document.source != "live" or document.phase != "finished":
                raise ValueError("Periodic result is not a finished live report")
        except (OSError, ValueError, TimeoutError):
            changed = add_event(
                self._change(self._state, last_outcome="unavailable"),
                "result_unavailable",
                "The last periodic report could not be read. "
                "No result or security change is assumed.",
                scan_id=self._state.last_scan_id,
                outcome="unavailable",
                occurred_at=self._time(),
            )
            await self._persist(changed)
            return
        comparable = [
            device
            for device in document.devices
            if device.comparison and device.comparison.status == "available"
        ]
        counts = MonitoringCounts(
            device_count=len(document.devices),
            finding_count=len(document.findings),
            completed_count=document.coverage.service_completed_count,
            unfinished_count=document.unfinished_device_count,
            comparable_device_count=len(comparable),
            changed_device_count=sum(
                device.comparison.added_count > 0 or device.comparison.not_observed_count > 0
                for device in comparable
            ),
        )
        changed = add_event(
            self._change(self._state, last_outcome=document.state),
            "result",
            f"{counts.device_count} device observations; {counts.completed_count} checks finished; "
            f"{counts.unfinished_count} unfinished; {counts.finding_count} review items. "
            f"{counts.comparable_device_count} device checks were comparable; "
            f"{counts.changed_device_count} had recorded feature changes. "
            "Missing responses do not establish removal or a verified fix.",
            scan_id=document.scan_id,
            outcome=document.state,
            counts=counts,
            occurred_at=self._time(),
        )
        if self._state.enabled and any(
            error.get("code") == "NETWORK_INTERRUPTED" for error in document.errors
        ):
            changed = add_event(
                self._change(
                    changed, enabled=False, next_check_at=None, pause_reason="network_unavailable"
                ),
                "paused",
                "A periodic check could not verify the network connection. Confirm "
                "the current network before enabling periodic checks again.",
                occurred_at=self._time(),
            )
            self._approved_context = None
            self._next_due = None
        await self._persist(changed)

    async def _submit(self, body, approved_context):
        from app.api.scans import _create_validated_live_scan

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/live-scans",
                "headers": [],
                "app": self.app,
            }
        )
        return await _create_validated_live_scan(request, body, approved_context=approved_context)

    async def tick(self, now=None):
        async with self._lock:
            await self._ensure_loaded()
            if self._closed or not self._available:
                return
            try:
                await self._record_result()
                if not self._state.enabled or self._next_due is None:
                    return
                now = self.clock() if now is None else now
                last = self._last_tick
                self._last_tick = now
                if last is not None and (now < last or now - last > SUSPEND_GAP_SECONDS):
                    await self._defer(
                        now,
                        "The app was delayed or this computer slept. Missed checks "
                        "will not be replayed; the next check is one interval from now.",
                    )
                    return
                if now < self._next_due:
                    return
                if self.app.state.supervisor.active_scan_count:
                    await self._defer(
                        now,
                        "Another scan or report explanation is running. "
                        "This periodic check was skipped; the next interval is scheduled.",
                    )
                    return
                try:
                    interface, context = await self._capture(self._state.scope)
                except HTTPException:
                    await self._pause(
                        "network_changed",
                        "The current network range could not be "
                        "matched to the approved range. Confirm it before enabling "
                        "periodic checks again.",
                    )
                    return
                except (OSError, ValueError, SnapshotUnavailable, TimeoutError):
                    await self._pause(
                        "network_unavailable",
                        "The current network connection could "
                        "not be verified. Confirm it before enabling periodic checks again.",
                    )
                    return
                if interface != self._approved_interface or context != self._approved_context:
                    await self._pause(
                        "network_changed",
                        "The network connection changed. Confirm "
                        "the current network before enabling periodic checks again.",
                    )
                    return
                if self._closed:
                    return
                if self.app.state.supervisor.active_scan_count:
                    await self._defer(
                        now,
                        "Another scan or report explanation is running. "
                        "This periodic check was skipped; the next interval is scheduled.",
                    )
                    return
                body = ScanCreateRequest(
                    mode="discover",
                    cidr=self._state.scope,
                    authorised=True,
                    confirmed_scope=self._state.scope,
                    profile="light",
                )
                try:
                    async with asyncio.timeout(SUBMISSION_TIMEOUT):
                        response = await self.submit(body, deepcopy(self._approved_context))
                except TimeoutError:
                    await self._pause(
                        "submission_failed",
                        "The periodic check could not be confirmed before the time limit. "
                        "Review saved reports before enabling periodic checks again.",
                    )
                    return
                except HTTPException as exc:
                    if exc.status_code == 429:
                        await self._defer(
                            now,
                            "Another scan or report explanation is running. "
                            "This periodic check was skipped; the next interval is scheduled.",
                        )
                    else:
                        await self._pause(
                            "network_changed" if exc.status_code == 409 else "submission_failed",
                            "The periodic check could not start under the approved conditions. "
                            "Confirm the current settings before enabling periodic checks again.",
                        )
                    return
                scan_id = response["scan_id"]
                interval = self._state.interval_minutes * 60
                self._next_due = now + interval
                changed = add_event(
                    self._change(
                        self._state,
                        last_scan_id=scan_id,
                        last_outcome="queued",
                        next_check_at=self._next_time(interval),
                    ),
                    "started",
                    "A periodic Light check started for the approved network range.",
                    scan_id=scan_id,
                    outcome="queued",
                    occurred_at=self._time(),
                )
                await self._persist(changed)
            except (MonitoringUnavailable, MonitoringRevisionConflict, OSError, TimeoutError):
                self._storage_failure()

    async def _run(self):
        while not self._stop.is_set():
            try:
                await self.tick()
            except Exception:
                async with self._lock:
                    if self._state.enabled:
                        try:
                            await self._pause(
                                "submission_failed",
                                "Periodic checks paused after an "
                                "unexpected local error. "
                                "Review Settings before enabling them again.",
                            )
                        except (
                            MonitoringUnavailable,
                            MonitoringRevisionConflict,
                            OSError,
                            TimeoutError,
                        ):
                            self._storage_failure()
            self._last_tick = self.clock()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=POLL_SECONDS)
            except TimeoutError:
                pass

    async def start(self):
        async with self._lock:
            await self._ensure_loaded()
            if self._task is None and not self._closed:
                self._task = asyncio.create_task(self._run(), name="periodic-light-checks")

    async def close(self):
        self._closed = True
        self._stop.set()
        self._approved_context = None
        self._next_due = None
        if self._task is not None:
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=SHUTDOWN_TIMEOUT)
            except TimeoutError:
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
