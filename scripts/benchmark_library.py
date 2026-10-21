"""Isolated, bounded synthetic JSON-library benchmark. Never scans or reads user data."""

import argparse
import asyncio
import contextlib
import hashlib
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from app.jobs.scheduling import capacity_slot
from app.schemas.scan import ScanDocument
from app.storage.annotations import AnnotationStore, TitleUpdate
from app.storage.device_inventory import DeviceInventory
from app.storage.json_store import JsonStore
from app.storage.library import search_reports


class CountedStore(JsonStore):
    reads = 0

    def _load_scan(self, scan_id):
        self.reads += 1
        return super()._load_scan(scan_id)


def synthetic_report(*, rich=False, active=False):
    scan_id = str(uuid4())
    devices, services = [], []
    if rich:
        for index in range(16):
            device_id = f"synthetic-{index}"
            devices.append(
                {
                    "device_id": device_id,
                    "scan_id": scan_id,
                    "ip": f"192.168.56.{index + 10}",
                    "hostname": f"Synthetic device {index + 1}",
                    "mac": f"02:00:00:00:00:{index + 1:02x}",
                }
            )
            for port in (22, 80, 139, 443, 445, 554, 8000, 8080):
                services.append(
                    {
                        "service_id": f"{device_id}-tcp-{port}",
                        "device_id": device_id,
                        "port": port,
                        "state": "open",
                        "name": "synthetic feature",
                        "script_results": [
                            {"script_id": "synthetic-evidence", "output": "x" * 512}
                        ],
                    }
                )
    return ScanDocument(
        scan_id=scan_id,
        source="live",
        state="running" if active else "completed",
        phase="service_scan" if active else "finished",
        analysis_status="not_started" if active else "ready",
        policy={"profile": "light", "allowed_network": "192.168.56.0/24"},
        target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
        devices=devices,
        services=services,
    )


async def mixed_load(store):
    """Actual JSON/checkpoint and admission code, but no scanner/provider subprocess."""
    document = await store.create_scan(synthetic_report(rich=True, active=True))
    capacity, started, progressed = asyncio.Semaphore(1), asyncio.Event(), asyncio.Event()
    writes, reads, overlap = [], [], []

    async def worker():
        async with capacity_slot(capacity, timeout_s=5):
            try:
                while True:
                    before = perf_counter()
                    # Shield a started atomic write and join it before the terminal
                    # checkpoint, so cancellation cannot leave a detached writer.
                    save = asyncio.create_task(
                        store.update_scan(document.scan_id, lambda current: current.model_copy())
                    )
                    try:
                        await asyncio.shield(save)
                    except asyncio.CancelledError:
                        await save
                        raise
                    writes.append(perf_counter() - before)
                    if any(not read.done() for read in reads):
                        overlap.append(True)
                    if len(writes) >= 3:
                        progressed.set()
                    started.set()
                    await asyncio.sleep(0.02)
            finally:
                await store.update_scan(
                    document.scan_id,
                    lambda current: current.model_copy(
                        update={"state": "cancelled", "phase": "finished"}
                    ),
                )

    task = asyncio.create_task(worker())
    await asyncio.wait_for(started.wait(), 10)

    async def timed(call):
        before = perf_counter()
        response = await asyncio.to_thread(call)
        return response, round(perf_counter() - before, 4)

    search = asyncio.create_task(timed(lambda: search_reports(store, limit=24)))
    inventory = asyncio.create_task(timed(lambda: DeviceInventory(store).list(limit=24)))
    reads.extend((search, inventory))
    try:
        # Keep checkpointing while reads run, rather than cancelling during
        # the first idle pause before any mixed-load write has occurred.
        await asyncio.wait_for(progressed.wait(), 10)
        before = perf_counter()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        cancellation_s = round(perf_counter() - before, 4)
        search_result, inventory_result = await asyncio.gather(search, inventory)
    finally:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await asyncio.gather(search, inventory, return_exceptions=True)
    saved = await store.load_scan(document.scan_id)
    assert saved.state == "cancelled" and saved.phase == "finished"
    async with capacity_slot(capacity, timeout_s=1):
        pass
    return {
        "search_seconds": search_result[1],
        "search_total": search_result[0]["total"],
        "inventory_seconds": inventory_result[1],
        "inventory_total": inventory_result[0]["total"],
        "inventory_warnings": inventory_result[0]["warnings"],
        "checkpoint_writes": len(writes),
        "checkpoint_saves_completed_while_reads_pending": len(overlap),
        "max_checkpoint_seconds": round(max(writes), 4),
        "synthetic_cancel_and_terminal_save_seconds": cancellation_s,
        "terminal_cancel_saved": True,
        "capacity_released": True,
        "not_a_live_scanner_cancellation_measurement": True,
    }


async def benchmark(root, counts=(32, 600), *, rich=False):
    results = []
    for count in counts:
        if not 1 <= count <= 1000:
            raise ValueError("Benchmark count must be 1-1000")
        folder = root / str(count)
        folder.mkdir(parents=True, exist_ok=False)
        store = CountedStore(folder)
        ids = []
        for _ in range(count):
            document = synthetic_report(rich=rich)
            store._create_scan(document)
            ids.append(document.scan_id)
        original = {
            scan_id: hashlib.sha256(
                (folder / "scans" / scan_id / "scan.json").read_bytes()
            ).digest()
            for scan_id in ids
        }
        row = {
            "reports": count,
            "rich": rich,
            "devices_per_report": 16 if rich else 0,
            "services_per_report": 128 if rich else 0,
            "source_json_bytes": sum(
                (folder / "scans" / scan_id / "scan.json").stat().st_size for scan_id in ids
            ),
        }
        for label in ("cold", "warm"):
            before, start = store.reads, perf_counter()
            response = await asyncio.to_thread(search_reports, store, limit=24)
            row[label] = {
                "seconds": round(perf_counter() - start, 4),
                "full_json_reads": store.reads - before,
            }
            assert response["total"] == count and len(response["items"]) == min(24, count)
        start = perf_counter()
        notes = AnnotationStore(store)
        await asyncio.gather(
            asyncio.to_thread(search_reports, store, limit=24),
            notes.update(
                ids[0], title=TitleUpdate(expected_revision=1, title="Synthetic concurrent edit")
            ),
        )
        row["concurrent_read_write_s"] = round(perf_counter() - start, 4)
        assert (await notes.load(ids[0])).title == "Synthetic concurrent edit"
        start = perf_counter()
        search = asyncio.create_task(asyncio.to_thread(search_reports, store, limit=24))
        # The same event loop must remain responsive while library I/O is offloaded.
        await asyncio.sleep(0.01)
        row["control_task_latency_s"] = round(perf_counter() - start, 4)
        await search
        if rich:
            row["mixed_load"] = await mixed_load(store)
        row["source_files_preserved"] = all(
            hashlib.sha256((folder / "scans" / scan_id / "scan.json").read_bytes()).digest()
            == original[scan_id]
            for scan_id in ids
        )
        assert row["source_files_preserved"]
        results.append(row)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rich", action="store_true", help="Include rich histories/mixed load")
    args = parser.parse_args()
    root = (
        Path(__file__).resolve().parents[1]
        / ".test-artifacts"
        / f"library-bench-{uuid4().hex[:10]}"
    )
    root.mkdir(parents=True, exist_ok=False)
    print(f"Synthetic benchmark artifacts: {root}", flush=True)
    result = asyncio.run(benchmark(root, rich=args.rich))
    (root / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
