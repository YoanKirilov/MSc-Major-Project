from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from .adapter import DemoFindingsAdapter


class DemoRunStore:
    def __init__(self, root: str | Path, adapter: DemoFindingsAdapter | None = None):
        self.root = Path(root)
        self.adapter = adapter or DemoFindingsAdapter()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self) -> dict:
        run_id = str(uuid4())
        payload = {
            "run_id": run_id,
            "source": "demo",
            "state": "completed",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "result": self.adapter.load(),
        }
        path = self.root / f"{run_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
        return payload

    def load(self, run_id: str) -> dict:
        path = self.root / f"{UUID(run_id)}.json"
        return json.loads(path.read_text(encoding="utf-8"))
