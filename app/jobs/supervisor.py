from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Callable
from ipaddress import IPv4Address
from typing import Any

from app.risk.engine import evaluate_device
from app.profiling.classifier import classify_device
from app.scanner.commands import (
    DEEP_PROFILE,
    DEEP_UDP_PORTS,
    PORTS,
    UDP_PORTS,
    discovery_command,
    host_command,
)
from app.scanner.parser import parse_discovery, parse_host
from app.scanner.mdns import browse_mdns
from app.scanner.runner import ProcessResult, run_process
from app.storage.json_store import JsonStore
from app.schemas.common import iso_z, utc_now
from app.schemas.scan import ExplanationRecord, ScanDocument


logger = logging.getLogger(__name__)


class ScanSupervisor:
    def __init__(
        self,
        store: JsonStore,
        nmap_path: str = "nmap",
        process_runner=run_process,
        explanation_service=None,
        mdns_browser=browse_mdns,
        max_concurrent_scans: int = 2,
    ):
        self.store = store
        self.nmap_path = nmap_path
        self.process_runner = process_runner
        self.explanation_service = explanation_service
        self.mdns_browser = mdns_browser
        self.max_concurrent_scans = max(1, max_concurrent_scans)
        self._tasks: dict[str, asyncio.Task] = {}
        self._analysis_tasks: dict[str, asyncio.Task] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._admission = asyncio.Lock()
        self._analysis_capacity = asyncio.Semaphore(1)

    def is_active(self, scan_id: str | None = None) -> bool:
        if scan_id is not None:
            task = self._tasks.get(scan_id)
            return task is not None and not task.done()
        return any(not task.done() for task in self._tasks.values())

    @property
    def active_scan_count(self) -> int:
        return sum(not task.done() for task in self._tasks.values())

    @property
    def active_scan_ids(self) -> tuple[str, ...]:
        return tuple(scan_id for scan_id, task in self._tasks.items() if not task.done())

    def has_capacity(self) -> bool:
        return self.active_scan_count < self.max_concurrent_scans

    def is_analysis_active(self, scan_id: str) -> bool:
        task = self._analysis_tasks.get(scan_id)
        return task is not None and not task.done()

    async def start(self, scan_id: str) -> None:
        async with self._admission:
            if not self.has_capacity():
                raise RuntimeError("SCAN_CAPACITY")
            cancel_event = asyncio.Event()
            self._cancel_events[scan_id] = cancel_event
            self._tasks[scan_id] = asyncio.create_task(self._run(scan_id, cancel_event))

    async def request_explanations(self, scan_id: str) -> None:
        """Reword a saved result without starting another network scan."""
        async with self._admission:
            if self.is_active(scan_id) or self.is_analysis_active(scan_id):
                raise RuntimeError("SCAN_BUSY")
            document = await self.store.load_scan(scan_id)
            if document.source != "live" or document.state not in {"completed", "partial"}:
                raise RuntimeError("SCAN_NOT_READY")
            if document.phase != "finished" or not document.findings:
                raise RuntimeError("SCAN_NOT_READY")
            if document.ai_requests_used >= 12:
                raise RuntimeError("AI_REQUEST_LIMIT")
            if self.explanation_service is None:
                raise RuntimeError("AI_NOT_CONFIGURED")
            if not (await self.store.load_settings()).ai_enabled:
                raise RuntimeError("AI_DISABLED")
            await self._checkpoint(scan_id, lambda current: current.model_copy(update={
                "phase": "analysis",
            }))
            self._analysis_tasks[scan_id] = asyncio.create_task(self._run_explanations(scan_id))

    async def refresh_guidance(self, scan_id: str, expected_revision: int) -> ScanDocument:
        from app.risk.guidance import refresh_guidance

        async with self._admission:
            if self.is_active(scan_id) or self.is_analysis_active(scan_id):
                raise RuntimeError("SCAN_BUSY")
            return await self.store.update_scan(scan_id, refresh_guidance, expected_revision)

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
        analysis_tasks = list(self._analysis_tasks.values())
        for task in analysis_tasks:
            task.cancel()
        if analysis_tasks:
            await asyncio.gather(*analysis_tasks, return_exceptions=True)
        self._tasks.clear()
        self._analysis_tasks.clear()
        self._cancel_events.clear()

    async def reconcile_incomplete(self) -> None:
        """Close persisted jobs that cannot survive a process restart."""
        for scan_id in await self.store.list_incomplete_scan_ids():
            try:
                await self._checkpoint(
                    scan_id,
                    lambda current: self._interrupted_document(current),
                )
            except Exception:
                logger.exception("Failed to reconcile interrupted scan %s", scan_id)

    async def _checkpoint(self, scan_id: str, mutate: Callable[[Any], Any]) -> None:
        await self.store.update_scan(scan_id, mutate)

    async def _local_hostname(self, ip: str) -> str | None:
        try:
            hostname, _, _ = await asyncio.wait_for(asyncio.to_thread(socket.gethostbyaddr, ip), timeout=1.0)
        except (OSError, asyncio.TimeoutError):
            return None
        return hostname[:255] if hostname else None

    @staticmethod
    def _interrupted_document(current):
        if current.phase == "analysis" and current.state in {"completed", "partial"}:
            finished_at = iso_z(utc_now())
            existing = {record.finding_id: record for record in current.explanations}
            explanations = []
            for finding in current.findings:
                record = existing.get(finding.finding_id)
                if record is not None and record.status == "ready":
                    explanations.append(record)
                else:
                    explanations.append(ExplanationRecord(
                        finding_id=finding.finding_id,
                        status="fallback",
                        source="fixed",
                        completed_at=finished_at,
                        fallback_reason="process_restarted",
                        content=finding.fixed_explanation,
                    ))
            return current.model_copy(update={
                "phase": "finished",
                "explanations": explanations,
                "warnings": [*current.warnings, {
                    "code": "AI_EXPLANATION_INTERRUPTED",
                    "message": "Plain-language AI wording was interrupted; fixed guidance is shown.",
                }],
            })
        coverage = current.coverage.model_copy(deep=True)
        for target in coverage.targets:
            if target.service_status in {"pending", "running"}:
                target.service_status = "cancelled"
                target.reason_code = "process_restarted"
        coverage.service_stage_complete = False
        state = "partial" if current.devices else "failed"
        return current.model_copy(update={
            "state": state,
            "phase": "finished",
            "finished_at": iso_z(utc_now()),
            "coverage": coverage,
            "errors": [
                *current.errors,
                {
                    "code": "SCAN_INTERRUPTED",
                    "message": "The application stopped before this scan completed.",
                    "device_id": None,
                },
            ],
        })

    async def _run(self, scan_id: str, cancel_event: asyncio.Event) -> None:
        try:
            document = await self.store.load_scan(scan_id)
            settings = await self.store.load_settings()
            interface = document.policy.get("interface", settings.interface)
            retain_raw_xml = document.policy.get("retain_raw_xml", settings.retain_raw_xml)
            nmap_observed: set[str] = set()
            mdns_observed: set[str] = set()
            initial_phase = "discovery" if document.target.get("mode") == "discover" else "service_scan"
            await self._checkpoint(scan_id, lambda current: current.model_copy(update={
                "state": "running",
                "phase": initial_phase,
                "started_at": iso_z(utc_now()),
            }))
            target_hosts = tuple(document.target.get("hosts", []))
            if document.target.get("mode") == "discover":
                cidr = document.target.get("cidr")
                result = await self.process_runner(
                    discovery_command(self.nmap_path, cidr, interface), 45, cancel_event
                )
                if retain_raw_xml and result.stdout:
                    await self.store.save_raw_output(scan_id, "discovery.xml", result.stdout)
                if result.cancelled:
                    cancel_event.set()
                    target_hosts = ()
                elif result.timed_out or result.overflow or result.returncode != 0:
                    raise RuntimeError("Discovery did not complete")
                if not cancel_event.is_set():
                    candidates = tuple(target.ip for target in document.coverage.targets)
                    nmap_observed = set(parse_discovery(result.stdout, candidates))
                    observations = []
                    if document.policy.get("mdns_enabled"):
                        try:
                            observations = await self.mdns_browser(
                                document.policy["allowed_network"],
                                document.policy["mdns_interface_ip"],
                                cancel_event,
                            )
                            mdns_observed = {item.ip for item in observations if item.ip in candidates}
                        except Exception:
                            logger.exception("mDNS discovery failed for scan %s", scan_id)
                            await self._checkpoint(scan_id, lambda current: current.model_copy(update={
                                "warnings": [*current.warnings, {
                                    "code": "MDNS_UNAVAILABLE",
                                    "message": "Extra device announcements could not be checked; Nmap results remain available.",
                                }],
                            }))
                    observed = nmap_observed | mdns_observed
                    target_hosts = tuple(sorted(observed, key=IPv4Address)) if not cancel_event.is_set() else ()

                    def commit_discovery(current):
                        coverage = current.coverage.model_copy(deep=True)
                        for target in coverage.targets:
                            if target.ip in observed:
                                target.discovery_status = "observed"
                                target.service_status = "pending"
                                target.discovery_sources = [
                                    source for source, found in (("nmap", nmap_observed), ("mdns", mdns_observed))
                                    if target.ip in found
                                ]
                            else:
                                target.discovery_status = "not_seen"
                                target.service_status = "skipped"
                                target.reason_code = "not_observed"
                        coverage.discovered_count = len(observed)
                        coverage.discovery_complete = True
                        coverage.service_skipped_count = len(coverage.targets) - len(observed)
                        return current.model_copy(update={
                            "phase": "service_scan",
                            "coverage": coverage,
                            "observations": observations,
                        })

                    if not cancel_event.is_set():
                        await self._checkpoint(scan_id, commit_discovery)
            elif not cancel_event.is_set():
                await self._checkpoint(scan_id, lambda current: current.model_copy(update={
                    "phase": "service_scan",
                    "coverage": current.coverage.model_copy(update={"discovery_complete": False}),
                }))
            for ip in target_hosts:
                if cancel_event.is_set():
                    break
                def mark_running(current, ip=ip):
                    coverage = current.coverage.model_copy(deep=True)
                    coverage.service_attempted_count += 1
                    for target in coverage.targets:
                        if target.ip == ip:
                            target.service_status = "running"
                            target.reason_code = None
                    return current.model_copy(update={"coverage": coverage})

                await self._checkpoint(scan_id, mark_running)
                profile = document.policy.get("profile", "light")
                deep = profile == DEEP_PROFILE
                result: ProcessResult = await self.process_runner(
                    host_command(
                        self.nmap_path,
                        ip,
                        DEEP_PROFILE if deep else "light",
                        interface,
                    ),
                    960 if deep else 75,
                    cancel_event,
                )
                if retain_raw_xml and result.stdout:
                    await self.store.save_raw_output(
                        scan_id, f"host-{ip.replace('.', '-')}.xml", result.stdout
                    )
                if result.cancelled:
                    cancel_event.set()
                    await self._checkpoint(
                        scan_id,
                        lambda current, ip=ip: self._mark_host_failure(
                            current, ip, "cancelled", "HOST_SCAN_CANCELLED", cancelled=True
                        ),
                    )
                    break
                if result.timed_out or result.overflow or result.returncode != 0:
                    status = "timed_out" if result.timed_out else "failed"
                    await self._checkpoint(
                        scan_id,
                        lambda current, ip=ip, status=status: self._mark_host_failure(
                            current, ip, status, "HOST_SCAN_FAILED"
                        ),
                    )
                    continue
                try:
                    device, services = parse_host(
                        result.stdout,
                        ip,
                        scan_id,
                        ("nmap_discovery" if ip in nmap_observed else "mdns_advertisement")
                        if document.target.get("mode") == "discover" else "known_host",
                        profile_tcp_ports=(PORTS if not deep else range(1, 65536)),
                        profile_udp_ports=UDP_PORTS if not deep else DEEP_UDP_PORTS,
                        fill_unknown=not deep,
                    )
                except ValueError:
                    await self._checkpoint(
                        scan_id,
                        lambda current, ip=ip: self._mark_host_failure(
                            current, ip, "failed", "HOST_RESULT_INVALID"
                        ),
                    )
                    continue
                if ip in nmap_observed or ip in mdns_observed:
                    device.reachability = "observed"
                    device.reachability_evidence = sorted(set([
                        *device.reachability_evidence,
                        "nmap_discovery_response" if ip in nmap_observed else "mdns_advertisement",
                    ]))
                if device.hostname is None:
                    device.hostname = await self._local_hostname(ip)
                device.profile = device.profile.model_validate(classify_device(device, services))
                findings = evaluate_device(device, services)
                def commit(current, device=device, services=services, findings=findings, ip=ip):
                    coverage = current.coverage.model_copy(deep=True)
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
            latest = await self.store.load_scan(scan_id)
            if cancel_event.is_set():
                final_state = "cancelled"
            elif latest.coverage.service_failed_count:
                final_state = "partial" if latest.coverage.service_completed_count else "failed"
            else:
                final_state = "completed"
            should_explain = (
                final_state in {"completed", "partial"}
                and document.policy.get("ai_enabled", settings.ai_enabled)
                and self.explanation_service is not None
                and bool(latest.findings)
            )
            await self._checkpoint(scan_id, lambda current: current.model_copy(update={
                "state": final_state,
                "phase": "analysis" if should_explain else "finished",
                "finished_at": iso_z(utc_now()),
                "coverage": current.coverage.model_copy(update={"service_stage_complete": not cancel_event.is_set()}),
            }))
            if should_explain:
                self._analysis_tasks[scan_id] = asyncio.create_task(
                    self._run_explanations(scan_id)
                )
        except Exception:
            logger.exception("Scan %s failed", scan_id)
            await self._checkpoint(scan_id, lambda current: current.model_copy(update={
                "state": "failed" if not current.devices else "partial",
                "phase": "finished",
                "finished_at": iso_z(utc_now()),
                "errors": [*current.errors, {"code": "SCAN_FAILED", "message": "The scan did not complete.", "device_id": None}],
            }))
        finally:
            self._cancel_events.pop(scan_id, None)
            self._tasks.pop(scan_id, None)

    async def _run_explanations(self, scan_id: str) -> None:
        try:
            async with self._analysis_capacity:
                await self.explanation_service.explain_scan(scan_id)
        except asyncio.CancelledError:
            await self._finish_explanations(scan_id, warning_code="AI_EXPLANATION_CANCELLED")
            raise
        except Exception:
            logger.exception("AI explanation failed for scan %s", scan_id)
            await self._finish_explanations(scan_id, warning_code="AI_EXPLANATION_FAILED")
        else:
            await self._finish_explanations(scan_id)
        finally:
            self._analysis_tasks.pop(scan_id, None)

    async def _finish_explanations(self, scan_id: str, warning_code: str | None = None) -> None:
        def finish(current):
            warnings = current.warnings
            if warning_code:
                warnings = [
                    *warnings,
                    {
                        "code": warning_code,
                        "message": "Plain-language AI wording was unavailable; fixed guidance is shown.",
                    },
                ]
            return current.model_copy(update={"phase": "finished", "warnings": warnings})

        try:
            await self._checkpoint(scan_id, finish)
        except (FileNotFoundError, ValueError):
            logger.warning("Could not finalize AI explanation state for scan %s", scan_id)

    @staticmethod
    def _mark_host_failure(current, ip, status, code, *, cancelled=False):
        coverage = current.coverage.model_copy(deep=True)
        if not cancelled:
            coverage.service_failed_count += 1
        for target in coverage.targets:
            if target.ip == ip:
                target.service_status = status
                target.reason_code = code.lower()
        if cancelled:
            return current.model_copy(update={"coverage": coverage})
        return current.model_copy(update={
            "coverage": coverage,
            "errors": [
                *current.errors,
                {
                    "code": code,
                    "message": "A host scan did not complete.",
                    "device_id": None,
                },
            ],
        })
