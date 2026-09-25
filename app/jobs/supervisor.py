from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Callable
from ipaddress import IPv4Address
from typing import Any

from app.profiling.classifier import classify_device
from app.risk.engine import evaluate_device
from app.scanner.commands import (
    DEEP_PROFILE,
    DEEP_UDP_PORTS,
    PORTS,
    UDP_PORTS,
    discovery_command,
    host_command,
)
from app.scanner.mdns import browse_mdns
from app.scanner.parser import parse_discovery_details, parse_host
from app.scanner.runner import ProcessResult, run_process
from app.schemas.common import iso_z, utc_now
from app.schemas.scan import ExplanationRecord, ScanDocument
from app.storage.json_store import JsonStore

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
        pihole_client=None,
    ):
        self.store = store
        self.nmap_path = nmap_path
        self.process_runner = process_runner
        self.explanation_service = explanation_service
        self.mdns_browser = mdns_browser
        self.pihole_client = pihole_client
        self.max_concurrent_scans = max(1, max_concurrent_scans)
        self._tasks: dict[str, asyncio.Task] = {}
        self._analysis_tasks: dict[str, asyncio.Task] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._admission = asyncio.Lock()
        self._analysis_capacity = asyncio.Semaphore(1)
        self._host_capacity = asyncio.Semaphore(2)
        self._detail_capacity = asyncio.Semaphore(2)
        self.details_timeout_s = 30
        self.host_stage_timeout_s = 1800

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
        return tuple(
            dict.fromkeys(
                scan_id
                for tasks in (self._tasks, self._analysis_tasks)
                for scan_id, task in tasks.items()
                if not task.done()
            )
        )

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
            if document.source != "live" or document.state not in {
                "completed",
                "partial",
                "failed",
                "cancelled",
            }:
                raise RuntimeError("SCAN_NOT_READY")
            if document.phase != "finished":
                raise RuntimeError("SCAN_NOT_READY")
            if self.explanation_service is None:
                raise RuntimeError("AI_NOT_CONFIGURED")
            await self._checkpoint(
                scan_id,
                lambda current: current.model_copy(
                    update={
                        "phase": "analysis",
                        "state": "running",
                        "analysis_status": "running",
                        "analysis_error": None,
                        "scan_outcome": current.scan_outcome or current.state,
                    }
                ),
            )
            self._analysis_tasks[scan_id] = asyncio.create_task(self._run_explanations(scan_id))

    async def refresh_guidance(self, scan_id: str, expected_revision: int) -> ScanDocument:
        from app.risk.guidance import refresh_guidance

        async with self._admission:
            if self.is_active(scan_id) or self.is_analysis_active(scan_id):
                raise RuntimeError("SCAN_BUSY")
            return await self.store.update_scan(scan_id, refresh_guidance, expected_revision)

    async def cancel(self, scan_id: str) -> bool:
        event = self._cancel_events.get(scan_id)
        task = self._analysis_tasks.get(scan_id)
        if event is None and (task is None or task.done()):
            return False
        if event is not None:
            event.set()
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            current = await self.store.load_scan(scan_id)
            if current.phase == "analysis":
                # A task cancelled before its coroutine starts cannot run its finally block.
                await self._finish_explanations(scan_id, warning_code="AI_EXPLANATION_CANCELLED")
            self._analysis_tasks.pop(scan_id, None)
        return True

    async def shutdown(self) -> None:
        for event in self._cancel_events.values():
            event.set()
        for task in self._analysis_tasks.values():
            task.cancel()
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
                await self.store.finish_scan(
                    scan_id,
                    lambda current: self._interrupted_document(current),
                )
            except Exception:
                logger.exception("Failed to reconcile interrupted scan %s", scan_id)

    async def _checkpoint(self, scan_id: str, mutate: Callable[[Any], Any]) -> None:
        await self.store.update_scan(scan_id, mutate)

    @staticmethod
    def _close_unfinished(current, reason: str, *, cancelled: bool = False):
        coverage = current.coverage.model_copy(deep=True)
        for target in coverage.targets:
            eligible = (
                current.target.get("mode") == "known_hosts" or target.discovery_status == "observed"
            )
            if eligible and target.service_status in {"pending", "running"}:
                target.service_status = "cancelled" if cancelled else "failed"
                target.reason_code = reason
                if not cancelled:
                    coverage.service_failed_count += 1
        coverage.service_stage_complete = False
        return current.model_copy(update={"coverage": coverage})

    async def _local_hostname(self, ip: str) -> str | None:
        try:
            hostname, _, _ = await asyncio.wait_for(
                asyncio.to_thread(socket.gethostbyaddr, ip), timeout=1.0
            )
        except (OSError, asyncio.TimeoutError):
            return None
        return hostname[:255] if hostname else None

    async def _enrich_names(self, scan_id: str, cancel_event: asyncio.Event) -> None:
        from app.scanner.names import add_name
        from app.scanner.pihole import apply_pihole_names

        document = await self.store.load_scan(scan_id)
        if cancel_event.is_set():
            return
        records = []
        warning = None
        if document.policy.get("pihole_enabled"):
            try:
                if self.pihole_client is None:
                    raise ValueError("Pi-hole is not configured")
                records = await asyncio.wait_for(
                    self.pihole_client.names(document.policy["allowed_network"]),
                    timeout=20,
                )
            except Exception:
                # Do not log external responses, URLs with credentials, or session IDs.
                warning = {
                    "code": "PIHOLE_UNAVAILABLE",
                    "message": (
                        "Pi-hole device names could not be read. Scan observations are "
                        "still available."
                    ),
                }

        def enrich(current):
            devices = [device.model_copy(deep=True) for device in current.devices]
            for device in devices:
                if device.hostname:
                    add_name(
                        device,
                        device.hostname,
                        device.hostname_source or "nmap",
                        device.observed_at,
                    )
                for observation in current.observations:
                    if observation.ip == device.ip:
                        add_name(
                            device, observation.advertised_name, "mdns", observation.observed_at
                        )
            apply_pihole_names(devices, records)
            for device in devices:
                services = [item for item in current.services if item.device_id == device.device_id]
                device.profile = device.profile.model_validate(classify_device(device, services))
            return current.model_copy(
                update={
                    "devices": devices,
                    "warnings": [
                        *current.warnings,
                        *getattr(records, "warnings", []),
                        *([warning] if warning else []),
                    ],
                }
            )

        await self._checkpoint(scan_id, enrich)

    async def _known_host_announcements(self, scan_id, cancel_event):
        document = await self.store.load_scan(scan_id)
        if (
            document.target.get("mode") != "known_hosts"
            or not document.policy.get("mdns_enabled")
            or cancel_event.is_set()
        ):
            return
        try:
            observations = await asyncio.wait_for(
                self.mdns_browser(
                    document.policy["allowed_network"],
                    document.policy["mdns_interface_ip"],
                    cancel_event,
                    target_ips=set(document.target["hosts"]),
                ),
                timeout=5,
            )
            observations = [o for o in observations if o.ip in document.target["hosts"]]
            await self._checkpoint(
                scan_id, lambda current: current.model_copy(update={"observations": observations})
            )
        except Exception:
            await self._checkpoint(
                scan_id,
                lambda current: current.model_copy(
                    update={
                        "warnings": [
                            *current.warnings,
                            {
                                "code": "MDNS_UNAVAILABLE",
                                "message": "Announcements could not be checked for this host.",
                            },
                        ]
                    }
                ),
            )

    async def _enrich_details(self, scan_id, cancel_event):
        from app.profiling.history import compare_history
        from app.scanner.details import detail, existing_details, netbios_name, network_details
        from app.scanner.mdns import MAX_ADVERTISEMENTS, MAX_UNIQUE_HOSTS

        document = await self.store.load_scan(scan_id)
        if not document.policy.get("extra_details_enabled") or cancel_event.is_set():
            return
        devices = [d.model_copy(deep=True) for d in document.devices]
        mdns_limit_reached = (
            len(document.observations) >= MAX_ADVERTISEMENTS
            or len({item.ip for item in document.observations}) >= MAX_UNIQUE_HOSTS
        )
        finished = set()

        async def enrich(device):
            services = [s for s in document.services if s.device_id == device.device_id]
            existing_details(device, services, document.observations)
            async with self._detail_capacity:
                if cancel_event.is_set():
                    return
                try:
                    await network_details(device, services, document.policy["allowed_network"])
                    async with self._host_capacity:
                        await netbios_name(
                            device,
                            services,
                            self.nmap_path,
                            self.process_runner,
                            cancel_event,
                            document.policy.get("interface"),
                        )
                    finished.add(device.device_id)
                except Exception:
                    detail(
                        device,
                        "web",
                        "Extra information",
                        "Some optional information could not be collected.",
                        "Bounded extra checks",
                        "unavailable",
                    )

        tasks = [asyncio.create_task(enrich(d)) for d in devices]
        cancellation = asyncio.create_task(cancel_event.wait())
        group = asyncio.gather(*tasks)
        try:
            await asyncio.wait(
                {group, cancellation},
                timeout=self.details_timeout_s,
                return_when=asyncio.FIRST_COMPLETED,
            )
        finally:
            for task in [*tasks, cancellation]:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, cancellation, return_exceptions=True)
            await asyncio.gather(group, return_exceptions=True)
        for device in devices:
            if device.device_id not in finished:
                detail(
                    device,
                    "web",
                    "Extra information",
                    "Some optional checks ran out of time or were cancelled.",
                    "Bounded extra checks",
                    "not_checked",
                )
            services = [s for s in document.services if s.device_id == device.device_id]
            device.profile = device.profile.model_validate(classify_device(device, services))
        comparison = document.model_copy(update={"devices": devices})
        history_warning = None
        try:
            async with asyncio.timeout(5):
                page = await self.store.list_scans(source="live", offset=0, limit=11)
                previous = []
                for entry in page["items"]:
                    if entry["scan_id"] != scan_id and entry.get("storage_status") == "ok":
                        try:
                            previous.append(await self.store.load_scan(entry["scan_id"]))
                        except (OSError, ValueError):
                            continue
                compare_history(comparison, previous[:10])
        except Exception:
            history_warning = {
                "code": "HISTORY_COMPARISON_UNAVAILABLE",
                "message": "History comparison could not finish; scan facts remain available.",
            }
        await self._checkpoint(
            scan_id,
            lambda current: current.model_copy(
                update={
                    "devices": devices,
                    "warnings": [
                        *current.warnings,
                        *([history_warning] if history_warning else []),
                        *(
                            [
                                {
                                    "code": "MDNS_LIMIT_REACHED",
                                    "message": "The announcement limit was reached; additional "
                                    "device names or features may not have been collected.",
                                }
                            ]
                            if mdns_limit_reached
                            else []
                        ),
                        *(
                            [
                                {
                                    "code": "EXTRA_DETAILS_INCOMPLETE",
                                    "message": "Extra checks unfinished; see device details.",
                                }
                            ]
                            if len(finished) != len(devices)
                            else []
                        ),
                    ],
                }
            ),
        )

    @staticmethod
    def _interrupted_document(current):
        if current.phase == "analysis" and current.analysis_status == "running":
            return current.model_copy(
                update={
                    "state": current.scan_outcome or "failed",
                    "phase": "finished",
                    "analysis_status": "failed",
                    "analysis_error": "process_restarted",
                    "finished_at": iso_z(utc_now()),
                }
            )
        if current.phase == "analysis" and current.state in {"completed", "partial"}:
            finished_at = iso_z(utc_now())
            existing = {record.finding_id: record for record in current.explanations}
            explanations = []
            for finding in current.findings:
                record = existing.get(finding.finding_id)
                if record is not None and record.status == "ready":
                    explanations.append(record)
                else:
                    explanations.append(
                        ExplanationRecord(
                            finding_id=finding.finding_id,
                            status="fallback",
                            source="fixed",
                            completed_at=finished_at,
                            fallback_reason="process_restarted",
                            content=finding.fixed_explanation,
                        )
                    )
            return current.model_copy(
                update={
                    "phase": "finished",
                    "explanations": explanations,
                    "warnings": [
                        *current.warnings,
                        {
                            "code": "AI_EXPLANATION_INTERRUPTED",
                            "message": (
                                "Plain-language AI wording was interrupted; fixed guidance is "
                                "shown."
                            ),
                        },
                    ],
                }
            )
        coverage = current.coverage.model_copy(deep=True)
        for target in coverage.targets:
            if target.service_status in {"pending", "running"}:
                target.service_status = "cancelled"
                target.reason_code = "process_restarted"
        coverage.service_stage_complete = False
        state = "partial" if current.devices else "failed"
        return current.model_copy(
            update={
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
            }
        )

    async def _run(self, scan_id: str, cancel_event: asyncio.Event) -> None:
        try:
            document = await self.store.load_scan(scan_id)
            settings = await self.store.load_settings()
            interface = document.policy.get("interface", settings.interface)
            retain_raw_xml = document.policy.get("retain_raw_xml", settings.retain_raw_xml)
            nmap_observed: set[str] = set()
            discovery_details = {}
            mdns_observed: set[str] = set()
            initial_phase = (
                "discovery" if document.target.get("mode") == "discover" else "service_scan"
            )
            await self._checkpoint(
                scan_id,
                lambda current: current.model_copy(
                    update={
                        "state": "running",
                        "phase": initial_phase,
                        "started_at": iso_z(utc_now()),
                    }
                ),
            )
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
                    discovery_details = parse_discovery_details(result.stdout, candidates)
                    nmap_observed = set(discovery_details)
                    observations = []
                    if document.policy.get("mdns_enabled"):
                        try:
                            observations = await self.mdns_browser(
                                document.policy["allowed_network"],
                                document.policy["mdns_interface_ip"],
                                cancel_event,
                            )
                            mdns_observed = {
                                item.ip for item in observations if item.ip in candidates
                            }
                        except Exception:
                            logger.exception("mDNS discovery failed for scan %s", scan_id)
                            await self._checkpoint(
                                scan_id,
                                lambda current: current.model_copy(
                                    update={
                                        "warnings": [
                                            *current.warnings,
                                            {
                                                "code": "MDNS_UNAVAILABLE",
                                                "message": (
                                                    "Extra device announcements could not be "
                                                    "checked; Nmap results "
                                                    "remain available."
                                                ),
                                            },
                                        ],
                                    }
                                ),
                            )
                    observed = nmap_observed | mdns_observed
                    target_hosts = (
                        tuple(sorted(observed, key=IPv4Address))
                        if not cancel_event.is_set()
                        else ()
                    )

                    def commit_discovery(current):
                        coverage = current.coverage.model_copy(deep=True)
                        for target in coverage.targets:
                            if target.ip in observed:
                                identity = discovery_details.get(target.ip, {})
                                target.discovery_mac = identity.get("mac")
                                target.discovery_hostname = identity.get("hostname")
                                target.discovery_vendor = identity.get("vendor")
                                target.discovery_status = "observed"
                                target.service_status = "pending"
                                target.discovery_sources = [
                                    source
                                    for source, found in (
                                        ("nmap", nmap_observed),
                                        ("mdns", mdns_observed),
                                    )
                                    if target.ip in found
                                ]
                            else:
                                target.discovery_status = "not_seen"
                                target.service_status = "skipped"
                                target.reason_code = "not_observed"
                        coverage.discovered_count = len(observed)
                        coverage.discovery_complete = True
                        coverage.service_skipped_count = len(coverage.targets) - len(observed)
                        return current.model_copy(
                            update={
                                "phase": "service_scan",
                                "coverage": coverage,
                                "observations": observations,
                            }
                        )

                    if not cancel_event.is_set():
                        await self._checkpoint(scan_id, commit_discovery)
            elif not cancel_event.is_set():
                await self._checkpoint(
                    scan_id,
                    lambda current: current.model_copy(
                        update={
                            "phase": "service_scan",
                            "coverage": current.coverage.model_copy(
                                update={"discovery_complete": False}
                            ),
                        }
                    ),
                )

            async def check_host(ip):
                if cancel_event.is_set():
                    return

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
                parsed = None
                parse_error_code = "HOST_RESULT_INVALID"
                for attempt in range(1, 3):

                    def mark_attempt(current, attempt=attempt):
                        coverage = current.coverage.model_copy(deep=True)
                        for target in coverage.targets:
                            if target.ip == ip:
                                target.attempts = attempt
                                target.reason_code = "retrying" if attempt > 1 else None
                        return current.model_copy(update={"coverage": coverage})

                    await self._checkpoint(scan_id, mark_attempt)
                    result: ProcessResult = await self.process_runner(
                        host_command(
                            self.nmap_path, ip, DEEP_PROFILE if deep else "light", interface
                        ),
                        960 if deep else 210,
                        cancel_event,
                    )
                    if result.cancelled or cancel_event.is_set() or result.overflow:
                        break
                    if not result.timed_out and result.returncode == 0:
                        try:
                            parsed = parse_host(
                                result.stdout,
                                ip,
                                scan_id,
                                ("nmap_discovery" if ip in nmap_observed else "mdns_advertisement")
                                if document.target.get("mode") == "discover"
                                else "known_host",
                                profile_tcp_ports=PORTS if not deep else range(1, 65536),
                                profile_udp_ports=UDP_PORTS if not deep else DEEP_UDP_PORTS,
                                fill_unknown=not deep,
                            )
                            break
                        except ValueError as exc:
                            parse_error_code = (
                                "HOST_SCAN_TIMEOUT"
                                if "timed out" in str(exc)
                                else "HOST_RESULT_INVALID"
                            )
                if retain_raw_xml and result.stdout:
                    await self.store.save_raw_output(
                        scan_id, f"host-{ip.replace('.', '-')}.xml", result.stdout
                    )
                if result.cancelled or cancel_event.is_set():
                    cancel_event.set()
                    await self._checkpoint(
                        scan_id,
                        lambda current, ip=ip: self._mark_host_failure(
                            current, ip, "cancelled", "HOST_SCAN_CANCELLED", cancelled=True
                        ),
                    )
                    return
                if result.timed_out or result.overflow or result.returncode != 0:
                    status = "timed_out" if result.timed_out else "failed"
                    failure_code = (
                        "HOST_SCAN_TIMEOUT"
                        if result.timed_out
                        else "HOST_OUTPUT_LIMIT"
                        if result.overflow
                        else "HOST_SCAN_FAILED"
                    )
                    await self._checkpoint(
                        scan_id,
                        lambda current, ip=ip, status=status: self._mark_host_failure(
                            current, ip, status, failure_code
                        ),
                    )
                    return
                if parsed is None:
                    await self._checkpoint(
                        scan_id,
                        lambda current, ip=ip: self._mark_host_failure(
                            current,
                            ip,
                            "timed_out" if parse_error_code == "HOST_SCAN_TIMEOUT" else "failed",
                            parse_error_code,
                        ),
                    )
                    return
                device, services = parsed
                identity = discovery_details.get(ip, {})
                from app.scanner.names import normalise_mac

                compatible = (
                    not device.mac
                    or not identity.get("mac")
                    or normalise_mac(device.mac) == normalise_mac(identity["mac"])
                )
                if compatible:
                    device.mac = device.mac or identity.get("mac")
                    device.vendor = device.vendor or identity.get("vendor")
                if ip in nmap_observed or ip in mdns_observed:
                    if ip in nmap_observed:
                        device.reachability = "observed"
                    elif device.reachability != "observed":
                        device.reachability = "advertised"
                    device.reachability_evidence = sorted(
                        set(
                            [
                                *device.reachability_evidence,
                                "nmap_discovery_response"
                                if ip in nmap_observed
                                else "mdns_advertisement",
                            ]
                        )
                    )
                from app.scanner.names import add_name

                if device.hostname:
                    add_name(device, device.hostname, "nmap", device.observed_at)
                    device.hostname_observed_at = device.observed_at
                if compatible:
                    add_name(device, identity.get("hostname"), "nmap_discovery", device.observed_at)
                add_name(device, await self._local_hostname(ip), "reverse_dns", device.observed_at)
                device.profile = device.profile.model_validate(classify_device(device, services))
                findings = evaluate_device(device, services)

                def commit(current, device=device, services=services, findings=findings, ip=ip):
                    coverage = current.coverage.model_copy(deep=True)
                    coverage.service_completed_count += 1
                    for target in coverage.targets:
                        if target.ip == ip:
                            target.service_status = "completed"
                            target.reason_code = None
                    return current.model_copy(
                        update={
                            "devices": [*current.devices, device],
                            "services": [*current.services, *services],
                            "findings": [*current.findings, *findings],
                            "coverage": coverage,
                        }
                    )

                await self._checkpoint(scan_id, commit)

            remaining_hosts = iter(target_hosts)

            async def worker():
                while not cancel_event.is_set():
                    ip = next(remaining_hosts, None)
                    if ip is None:
                        return
                    async with self._host_capacity:
                        await check_host(ip)

            workers = [asyncio.create_task(worker()) for _ in range(min(2, len(target_hosts)))]
            try:
                async with asyncio.timeout(self.host_stage_timeout_s):
                    await asyncio.gather(*workers)
            finally:
                for task in workers:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*workers, return_exceptions=True)
            await self._known_host_announcements(scan_id, cancel_event)
            await self._enrich_names(scan_id, cancel_event)
            await self._enrich_details(scan_id, cancel_event)
            latest = await self.store.load_scan(scan_id)
            if cancel_event.is_set():
                await self._checkpoint(
                    scan_id,
                    lambda current: self._close_unfinished(
                        current, "host_scan_cancelled", cancelled=True
                    ),
                )
                final_state = "cancelled"
            elif latest.coverage.service_failed_count:
                final_state = "partial" if latest.coverage.service_completed_count else "failed"
            else:
                final_state = "completed"
            should_explain = final_state != "cancelled" and self.explanation_service is not None
            await self._checkpoint(
                scan_id,
                lambda current: current.model_copy(
                    update={
                        "state": "running" if should_explain else final_state,
                        "scan_outcome": final_state,
                        "analysis_status": "running" if should_explain else "not_started",
                        "phase": "analysis" if should_explain else "finished",
                        "finished_at": None if should_explain else iso_z(utc_now()),
                        "coverage": current.coverage.model_copy(
                            update={
                                "service_stage_complete": not cancel_event.is_set()
                                and not current.coverage.service_failed_count,
                            }
                        ),
                    }
                ),
            )
            if should_explain:
                self._analysis_tasks[scan_id] = asyncio.create_task(self._run_explanations(scan_id))
                await self._analysis_tasks[scan_id]
        except asyncio.CancelledError:
            # The analysis task persists its cancellation state before propagating.
            pass
        except Exception as exc:
            logger.exception("Scan %s failed", scan_id)
            from app.storage.json_store import DocumentTooLarge

            code = (
                "RESULT_SIZE_LIMIT"
                if isinstance(exc, DocumentTooLarge)
                else "SCAN_TIME_LIMIT"
                if isinstance(exc, TimeoutError)
                else "SCAN_FAILED"
            )
            await self.store.finish_scan(
                scan_id,
                lambda current: self._close_unfinished(current, code.lower()).model_copy(
                    update={
                        "state": "failed" if not current.devices else "partial",
                        "phase": "finished",
                        "finished_at": iso_z(utc_now()),
                        "errors": [
                            *current.errors,
                            {
                                "code": code,
                                "message": (
                                    "The result reached the storage limit; "
                                    "earlier observations are "
                                    "saved."
                                )
                                if code == "RESULT_SIZE_LIMIT"
                                else (
                                    "The device-check time limit was reached; "
                                    "saved results remain available."
                                )
                                if code == "SCAN_TIME_LIMIT"
                                else "The scan did not complete.",
                                "device_id": None,
                            },
                        ],
                    }
                ),
            )
            if (
                code != "RESULT_SIZE_LIMIT"
                and self.explanation_service is not None
                and not cancel_event.is_set()
            ):
                await self.request_analysis_after_failure(scan_id)
        finally:
            self._cancel_events.pop(scan_id, None)
            self._tasks.pop(scan_id, None)

    async def _run_explanations(self, scan_id: str) -> None:
        try:
            async with asyncio.timeout(900):
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
            ready = not warning_code and current.analysis_status == "ready"
            cancelled = warning_code == "AI_EXPLANATION_CANCELLED"
            return current.model_copy(
                update={
                    "phase": "finished",
                    "finished_at": iso_z(utc_now()),
                    "state": "cancelled" if cancelled else (current.scan_outcome or "completed"),
                    "analysis_status": "ready" if ready else "failed",
                    "analysis_error": None
                    if ready
                    else warning_code or current.analysis_error or "invalid_provider_response",
                }
            )

        try:
            await self.store.finish_scan(scan_id, finish)
        except (FileNotFoundError, ValueError):
            logger.warning("Could not finalize AI explanation state for scan %s", scan_id)

    async def request_analysis_after_failure(self, scan_id: str) -> None:
        await self._checkpoint(
            scan_id,
            lambda current: current.model_copy(
                update={
                    "scan_outcome": current.state,
                    "state": "running",
                    "phase": "analysis",
                    "analysis_status": "running",
                    "finished_at": None,
                }
            ),
        )
        self._analysis_tasks[scan_id] = asyncio.create_task(self._run_explanations(scan_id))
        await self._analysis_tasks[scan_id]

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
        return current.model_copy(
            update={
                "coverage": coverage,
                "errors": [
                    *current.errors,
                    {
                        "code": code,
                        "message": f"The device check for {ip} did not complete ({status}).",
                        "device_id": None,
                        "target_ip": ip,
                    },
                ],
            }
        )
