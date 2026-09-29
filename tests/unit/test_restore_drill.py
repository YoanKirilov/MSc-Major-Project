from app.schemas.scan import ScanDocument
from app.storage.json_store import JsonStore
from scripts.check_restore import check_restore, fingerprints


def test_restore_drill_only_corrupts_a_copy(tmp_path):
    source = tmp_path / "source"
    store = JsonStore(source)
    doc = ScanDocument(
        scan_id="11111111-1111-1111-1111-111111111111",
        target={"mode": "demo", "hosts": []},
        state="completed",
        phase="finished",
    )
    store._create_scan(doc)
    store._update_scan(doc.scan_id, lambda d: d, None)
    before = fingerprints(source)
    result = check_restore(source, doc.scan_id, tmp_path / "artifacts")
    assert result["source_unchanged"]
    assert fingerprints(source) == before
