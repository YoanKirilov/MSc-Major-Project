import json

import pytest

from app.demo.adapter import DemoDataError, DemoFindingsAdapter


def test_demo_adapter_loads_explicit_demo_payload():
    payload = DemoFindingsAdapter().load()
    assert payload["mode"] == "demo"
    assert payload["label"] == "Demonstration data"
    assert len(payload["findings"]) == 8


def test_demo_adapter_rejects_malformed_payload(tmp_path):
    path = tmp_path / "findings.json"
    path.write_text(json.dumps({"mode": "live", "findings": []}), encoding="utf-8")
    with pytest.raises(DemoDataError):
        DemoFindingsAdapter(path).load()
