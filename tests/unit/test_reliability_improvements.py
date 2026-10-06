import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from app.jobs.supervisor import ScanSupervisor
from app.runtime_diagnostics import observe_asyncio_errors
from app.schemas.scan import ScanDocument
from app.storage.annotations import AnnotationStore, TitleUpdate
from app.storage.json_store import JsonStore


def prepare_notes(tmp_path):
    store = JsonStore(tmp_path)
    doc = ScanDocument(
        scan_id=str(uuid4()), target={"mode": "known_hosts", "hosts": ["192.168.0.2"]}
    )
    store._create_scan(doc)
    notes = AnnotationStore(store)
    notes._update(doc.scan_id, title=TitleUpdate(expected_revision=1, title="Previous title"))
    notes._update(doc.scan_id, title=TitleUpdate(expected_revision=2, title="Newest title"))
    return store, doc, notes, store._scan_dir(doc.scan_id)


def test_annotations_recover_without_overwriting_backup_or_scan(tmp_path):
    store, doc, notes, folder = prepare_notes(tmp_path)
    evidence = (folder / "scan.json").read_bytes()
    backup = (folder / "annotations.previous.json").read_bytes()
    store._atomic_write(folder / "annotations.json", "broken")
    recovered = notes._load(doc.scan_id)
    assert recovered.title == "Previous title" and recovered.revision == 4
    assert recovered.recovery_notice
    assert (folder / "annotations.previous.json").read_bytes() == backup
    assert (folder / "scan.json").read_bytes() == evidence
    assert next(folder.glob("annotations.corrupt-*.json")).read_text() == "broken"
    assert notes._load(doc.scan_id) == recovered  # Recovery is durable, not repeated.
    with pytest.raises(ValueError, match="changed"):
        notes._update(doc.scan_id, title=TitleUpdate(expected_revision=3, title="Stale"))
    updated = notes._update(doc.scan_id, title=TitleUpdate(expected_revision=4, title="Reviewed"))
    assert updated.revision == 5 and updated.title == "Reviewed"


def test_both_annotation_copies_invalid_are_not_reset(tmp_path):
    store, doc, notes, folder = prepare_notes(tmp_path)
    for name in ("annotations.json", "annotations.previous.json"):
        store._atomic_write(folder / name, "broken")
    with pytest.raises(ValueError):
        notes._load(doc.scan_id)
    assert (folder / "annotations.json").read_text() == "broken"


def test_missing_annotations_primary_recovers_backup(tmp_path):
    _, doc, notes, folder = prepare_notes(tmp_path)
    (folder / "annotations.json").unlink()
    assert notes._load(doc.scan_id).title == "Previous title"


@pytest.mark.asyncio
async def test_runtime_activity_is_live_and_cleared_on_failure(tmp_path):
    entered, release = asyncio.Event(), asyncio.Event()

    async def runner(*args):
        entered.set()
        await release.wait()
        raise RuntimeError("synthetic scanner error")

    supervisor = ScanSupervisor(JsonStore(tmp_path), process_runner=runner)
    task = asyncio.create_task(supervisor._run_scanner("example", ["test"], 1, asyncio.Event()))
    await entered.wait()
    progress = supervisor.runtime_progress("example")
    assert progress["scanner_checks_running"] == 1
    assert progress["last_scanner_event"] == "started"
    release.set()
    with pytest.raises(RuntimeError):
        await task
    assert supervisor.runtime_progress("example")["scanner_checks_running"] == 0
    assert supervisor.runtime_progress("example")["last_scanner_event"] == "returned"


@pytest.mark.asyncio
async def test_asyncio_diagnostics_delegate_all_errors_and_restore(caplog):
    loop = asyncio.get_running_loop()
    previous = loop.get_exception_handler()
    delegated = Mock()
    loop.set_exception_handler(delegated)
    try:
        with observe_asyncio_errors(loop) as observed:
            for error in (ConnectionResetError("secret peer value"), RuntimeError("secret URL")):
                loop.call_exception_handler({"exception": error, "message": "secret"})
            assert observed["count"] == 2
            assert observed["last_event"]["at"]
            assert delegated.call_count == 2
        assert loop.get_exception_handler() is delegated
        assert "secret" not in caplog.text
    finally:
        loop.set_exception_handler(previous)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows transport regression investigation")
def test_windows_shutdown_reset_reproduces_original_cleanup_traceback():
    from asyncio.proactor_events import _ProactorBasePipeTransport

    error = ConnectionResetError("synthetic reset")
    sock = Mock()
    sock.fileno.return_value = 1
    sock.shutdown.side_effect = error
    transport = SimpleNamespace(_called_connection_lost=False, _sock=sock, _protocol=Mock())
    with pytest.raises(ConnectionResetError):
        _ProactorBasePipeTransport._call_connection_lost(transport, None)
    transport._protocol.connection_lost.assert_called_once_with(None)
    sock.close.assert_not_called()  # Demonstrates why suppressing the error is not a fix.
