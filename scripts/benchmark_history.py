"""Measure synthetic JSON history search; never read normal report storage."""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.scan import Device, ScanDocument
from app.storage.json_store import JsonStore
from app.storage.library import search_reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="100,500,1000")
    args = parser.parse_args()
    sizes = [int(value) for value in args.sizes.split(",")]
    if not sizes or any(size < 1 or size > 2000 for size in sizes):
        parser.error("Use report counts between 1 and 2000")
    root = Path(__file__).resolve().parents[1]
    run = root / ".test-artifacts" / f"history-benchmark-{uuid4().hex[:10]}"
    results = []
    for size in sizes:
        store = JsonStore(run / str(size))
        for index in range(size):
            scan_id = str(uuid4())
            doc = ScanDocument(
                scan_id=scan_id,
                state="completed",
                phase="finished",
                target={"mode": "known_hosts", "hosts": ["192.168.0.10"]},
                policy={"profile": "light", "allowed_network": "192.168.0.0/24"},
                devices=[
                    Device(
                        device_id=str(uuid4()),
                        scan_id=scan_id,
                        ip="192.168.0.10",
                        hostname=f"Synthetic device {index}",
                    )
                ],
            )
            store._create_scan(doc)
        trials = []
        for _ in range(4):
            started = time.perf_counter()
            found = search_reports(store, q="synthetic device")
            trials.append(round(time.perf_counter() - started, 4))
            assert found["total"] == size and not found["warnings"]
        results.append(
            {
                "reports": size,
                "cold_s": trials[0],
                "warm_trials_s": trials[1:],
                "warm_median_s": statistics.median(trials[1:]),
                "cached_entries": len(store.library_cache.entries),
                "cache_bytes": store.library_cache.size,
            }
        )
    output = {
        "method": "One device per synthetic report, four identical searches per library, "
        "no normal data or provider calls. Cold means a fresh in-process cache, "
        "not a cold OS disk cache.",
        "results": results,
    }
    (run / "results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    print(f"Artifacts: {run}")


if __name__ == "__main__":
    main()
