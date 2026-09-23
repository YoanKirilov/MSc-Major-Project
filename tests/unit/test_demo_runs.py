import json

from app.demo.runs import DemoRunStore


def test_demo_run_is_persisted_as_local_json(tmp_path):
    store = DemoRunStore(tmp_path)
    created = store.create()
    saved_path = tmp_path / f"{created['run_id']}.json"
    assert saved_path.exists()
    loaded = store.load(created["run_id"])
    assert loaded["source"] == "demo"
    assert loaded["result"]["mode"] == "demo"
    assert json.loads(saved_path.read_text(encoding="utf-8"))["run_id"] == created["run_id"]
