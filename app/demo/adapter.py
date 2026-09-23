from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DemoDataError(ValueError):
    pass


class DemoFindingsAdapter:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else Path(__file__).with_name("findings.json")

    def load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DemoDataError("Demo data is unavailable or malformed.") from exc
        if payload.get("mode") != "demo" or not isinstance(payload.get("findings"), list):
            raise DemoDataError("Demo data does not match the expected format.")
        return payload
