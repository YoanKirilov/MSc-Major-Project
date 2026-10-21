"""Bounded durable scan-start intentions; receipts never authorise a new scan."""

import asyncio
import hashlib
import json
from uuid import UUID, uuid4

from fastapi import HTTPException
from filelock import FileLock
from pydantic import Field, field_validator

from app.jobs.transitions import close_unfinished
from app.schemas.common import StrictModel, iso_z, utc_now


class StartReceipt(StrictModel):
    scan_id: UUID
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request: dict
    created_at: str
    state: str = Field(pattern=r"^(preparing|accepted|rejected|interrupted)$")
    error_status: int | None = None


class StartJournal(StrictModel):
    operations: dict[str, StartReceipt] = Field(default_factory=dict, max_length=1024)

    @field_validator("operations")
    @classmethod
    def canonical_ids(cls, value):
        if any(str(UUID(key)) != key for key in value):
            raise ValueError("Invalid start operation identifier")
        return value


class StartRequests:
    def __init__(self, store, supervisor):
        self.store, self.supervisor = store, supervisor
        self.path = store.data_root / "scan-starts.json"
        self.lock_path = store.data_root / "scan-starts.lock"
        self.admission = asyncio.Lock()
        self.tasks = {}

    def _load(self):
        backup = self.path.with_name("scan-starts.previous.json")
        if not self.path.exists() and not self.path.is_symlink() and not backup.exists():
            return StartJournal()
        # Never roll back an unknown intention into permission to submit it again.
        if self.path.stat().st_size > 1024 * 1024:
            raise ValueError("Scan-start journal size limit reached")
        return StartJournal.model_validate(self.store._read_json(self.path))

    def _transaction(self, operation, *, create=None, state=None, error_status=None):
        if self.lock_path.is_symlink():
            raise ValueError("Unsafe scan-start lock")
        with FileLock(str(self.lock_path), timeout=2):
            journal = self._load()
            record = journal.operations.get(operation)
            if create is not None and record is None:
                if len(journal.operations) >= 1024:
                    raise HTTPException(
                        409,
                        "Scan-start receipt capacity reached; saved reports remain available. "
                        "Maintenance is required before another new start.",
                    )
                record = create
                journal.operations[operation] = record
            elif state is not None:
                if record is None:
                    raise ValueError("Missing start receipt")
                record.state, record.error_status = state, error_status
            else:
                return record
            payload = journal.model_dump_json()
            if len(payload.encode()) > 1024 * 1024:
                raise ValueError("Scan-start journal size limit reached")
            self.store._atomic_write(
                self.path, payload, self.path.with_name("scan-starts.previous.json")
            )
            return record

    async def _access(self, *args, **kwargs):
        try:
            return await asyncio.to_thread(self._transaction, *args, **kwargs)
        except (OSError, ValueError) as exc:
            raise HTTPException(
                503,
                "Scan-start receipts are unavailable. Do not repeat the start; "
                "saved reports remain available.",
            ) from exc

    async def _document(self, record):
        try:
            doc = await self.store.load_scan(record.scan_id)
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            raise HTTPException(
                503,
                "The original scan cannot be read right now; "
                "do not start a replacement to recover it.",
            ) from exc
        return doc

    async def status(self, operation):
        record = await self._access(operation)
        if record is None:
            raise HTTPException(
                404, "This start is not recorded yet. No replacement scan was submitted."
            )
        doc = await self._document(record)
        if doc is not None and doc.policy.get("start_operation_id") == operation:
            # In-flight creation is not confirmation that admission has finished.
            admitted = self.supervisor.is_active(str(record.scan_id)) or doc.phase == "finished"
            if record.state == "accepted" or admitted:
                return {
                    "state": "accepted",
                    "scan_id": str(record.scan_id),
                    "request": record.request,
                }
        state = record.state
        if state == "preparing" and operation not in self.tasks:
            state = "interrupted"
        if state == "accepted":
            state = "report_unavailable"
        return {
            "state": state,
            "scan_id": None,
            "request": record.request,
            "error_status": record.error_status,
        }

    async def submit(self, body, create, validate_recovery, *, retry_of=None):
        operation = str(body.operation_id)
        payload = body.model_dump(mode="json", exclude={"operation_id"})
        if retry_of is not None:
            payload["retry_of"] = retry_of
        if not body.confirmed_scope:
            raise HTTPException(
                422, "Confirm the current network range before starting a recoverable scan."
            )
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        async with self.admission:
            record = await self._access(operation)
            if record is not None and record.fingerprint != fingerprint:
                raise HTTPException(
                    409,
                    "This start identifier belongs to different scan settings. "
                    "No new scan was started.",
                )
            task = self.tasks.get(operation)
            if record is None:
                if len(self.tasks) >= 5:
                    raise HTTPException(
                        429, "Other scan starts are being prepared; try again shortly."
                    )
                record = await self._access(
                    operation,
                    create=StartReceipt(
                        scan_id=uuid4(),
                        fingerprint=fingerprint,
                        request=payload,
                        created_at=iso_z(utc_now()),
                        state="preparing",
                    ),
                )
                task = asyncio.create_task(self._run(operation, record, create), name="scan-start")
                self.tasks[operation] = task
                task.add_done_callback(
                    lambda finished: None if finished.cancelled() else finished.exception()
                )
        if task is not None:
            # A disconnected HTTP caller does not cancel or detach admission.
            return await asyncio.shield(task)
        status = await self.status(operation)
        if status["state"] != "accepted":
            raise HTTPException(
                409,
                "The previous start was not accepted or its report is unavailable. "
                "Read its saved status before choosing a new scan.",
            )
        await validate_recovery(await self._document(record))
        return {
            "scan_id": status["scan_id"],
            "state": "queued",
            "recovered": True,
            "status_url": f"/api/live-scans/{status['scan_id']}",
        }

    async def _run(self, operation, record, create):
        try:
            result = await create(str(record.scan_id), operation)
            await self._access(operation, state="accepted")
            return result
        except asyncio.CancelledError:
            doc = await self._document(record)
            if (
                doc is not None
                and not self.supervisor.is_active(str(record.scan_id))
                and doc.phase != "finished"
            ):
                await self.store.update_scan(
                    record.scan_id,
                    lambda current: close_unfinished(current, "scan_start_interrupted").model_copy(
                        update={
                            "state": "failed",
                            "scan_outcome": "failed",
                            "phase": "finished",
                            "finished_at": iso_z(utc_now()),
                            "analysis_status": "failed",
                            "analysis_error": "The app stopped while preparing this scan; "
                            "no completed checks are implied.",
                        }
                    ),
                )
            await self._access(operation, state="interrupted")
            raise
        except HTTPException as exc:
            if await self._document(record) is None:
                await self._access(operation, state="rejected", error_status=exc.status_code)
            raise
        finally:
            self.tasks.pop(operation, None)

    async def shutdown(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
