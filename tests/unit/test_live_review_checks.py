"""Offline checks for the opt-in helper; never launch a scanner or browser."""

import builtins
import sys
from uuid import uuid4

import pytest
from app.schemas.scan import ScanDocument
from scripts import live_review


def successful_results():
    return {
        "page_errors": [],
        "scan_submissions": 2,
        "refresh_kept_both_jobs": True,
        "automatic_reports_after_analysis": True,
    }


def test_scan_completion_is_distinct_from_a_successful_failed_report_workflow():
    complete = {
        "state": "completed",
        "phase": "finished",
        "target": {"mode": "discover"},
        "coverage": {"discovery_complete": True, "service_stage_complete": True},
    }
    assert live_review.completed_scan_pair([complete, complete])
    assert not live_review.completed_scan_pair([complete])
    for change in (
        {"state": "partial"},
        {"state": "failed"},
        {"phase": "analysis"},
        {"coverage": {"discovery_complete": False, "service_stage_complete": True}},
    ):
        assert not live_review.completed_scan_pair([complete, {**complete, **change}])
    # A known-host Deep check does not claim network discovery.
    known = {
        **complete,
        "target": {"mode": "known_hosts"},
        "coverage": {"discovery_complete": False, "service_stage_complete": True},
    }
    assert live_review.completed_scan_pair([complete, known])


def test_live_review_accepts_verified_browser_and_unchanged_existing_reports():
    live_review.require_review_success(
        successful_results(), {"normal_existing_reports_unchanged": True}
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("page_errors", ["report overflow at 320px"], "Browser errors"),
        ("page_errors", ["Uncaught exception"], "Browser errors"),
        ("scan_submissions", 1, "submission count"),
        ("scan_submissions", 3, "submission count"),
        ("refresh_kept_both_jobs", False, "preserve both"),
        ("automatic_reports_after_analysis", False, "navigation after analysis"),
    ],
)
def test_recorded_browser_failure_cannot_produce_a_success(field, value, message):
    results = {**successful_results(), field: value}
    with pytest.raises(RuntimeError, match=message):
        live_review.require_review_success(results, {"normal_existing_reports_unchanged": True})


def test_changed_existing_report_cannot_produce_a_success():
    with pytest.raises(RuntimeError, match="Existing normal reports changed"):
        live_review.require_review_success(
            successful_results(), {"normal_existing_reports_unchanged": False}
        )


def test_missing_browser_tools_fail_before_network_checks_or_artifact_creation(
    tmp_path, monkeypatch
):
    real_import = builtins.__import__

    def without_playwright(name, *args, **kwargs):
        if name == "playwright.sync_api":
            raise ModuleNotFoundError("Synthetic missing browser dependency")
        return real_import(name, *args, **kwargs)

    run = tmp_path / ".test-artifacts" / "never-created"
    monkeypatch.setattr(live_review, "ROOT", tmp_path)
    monkeypatch.setattr(builtins, "__import__", without_playwright)
    monkeypatch.setattr(live_review, "load_config", lambda: pytest.fail("Do not read app settings"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "live_review.py",
            "--authorised",
            "--scope",
            "192.168.56.0/24",
            "--host",
            "192.168.56.10",
            "--artifacts",
            str(run),
        ],
    )
    with pytest.raises(SystemExit) as error:
        live_review.main()
    assert error.value.code == 2
    assert not run.exists()


def stored_pair(run):
    ids = {}
    for profile, policy in (("light", "light"), ("deep", "deep-tcp-v1")):
        scan_id = str(uuid4())
        folder = run / "data" / "scans" / scan_id
        folder.mkdir(parents=True)
        document = ScanDocument(
            scan_id=scan_id,
            state="completed",
            phase="finished",
            target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
            policy={"profile": policy},
        )
        live_review.save(folder, "scan.json", document.model_dump(mode="json"))
        live_review.save(run, f"{profile}-id.json", {"scan_id": scan_id})
        ids[profile] = scan_id
    return ids


def test_saved_pair_reopens_only_existing_matching_finished_reports(tmp_path):
    ids = stored_pair(tmp_path)
    before = live_review.hashes(tmp_path)
    assert live_review.saved_pair(tmp_path) == (tmp_path / "data", ids)
    assert live_review.hashes(tmp_path) == before


@pytest.mark.parametrize(
    "update",
    [
        {"phase": "service_scan", "state": "running"},
        {"phase": "analysis", "state": "running"},
        {"phase": "finished", "state": "queued"},
        {"source": "demo"},
        {"policy": {"profile": "deep-tcp-v1"}},
    ],
)
def test_saved_pair_rejects_unfinished_or_mismatched_reports(tmp_path, update):
    ids = stored_pair(tmp_path)
    folder = tmp_path / "data" / "scans" / ids["light"]
    document = ScanDocument.model_validate_json((folder / "scan.json").read_bytes())
    live_review.save(
        folder, "scan.json", document.model_copy(update=update).model_dump(mode="json")
    )
    with pytest.raises(ValueError):
        live_review.saved_pair(tmp_path)


def test_saved_pair_rejects_an_unfinished_extra_job(tmp_path):
    stored_pair(tmp_path)
    document = ScanDocument(
        scan_id=str(uuid4()), target={"mode": "known_hosts", "hosts": ["192.168.56.11"]}
    )
    folder = tmp_path / "data" / "scans" / document.scan_id
    folder.mkdir()
    live_review.save(folder, "scan.json", document.model_dump(mode="json"))
    with pytest.raises(ValueError, match="Finish or cancel"):
        live_review.saved_pair(tmp_path)


def test_saved_review_requires_no_scan_submissions_or_evidence_changes():
    results = {
        **successful_results(),
        "scan_submissions": 0,
        "refresh_kept_both_jobs": None,
        "automatic_reports_after_analysis": None,
    }
    integrity = {
        "normal_existing_reports_unchanged": True,
        "saved_test_evidence_unchanged": True,
    }
    live_review.require_review_success(results, integrity, saved_only=True)
    with pytest.raises(RuntimeError, match="submission count"):
        live_review.require_review_success(
            {**results, "scan_submissions": 1}, integrity, saved_only=True
        )
    with pytest.raises(RuntimeError, match="Saved test evidence changed"):
        live_review.require_review_success(
            results, {**integrity, "saved_test_evidence_unchanged": False}, saved_only=True
        )


def test_saved_verification_cannot_start_a_backend_to_recover_unfinished_jobs(
    tmp_path, monkeypatch
):
    run = tmp_path / ".test-artifacts" / "unfinished"
    ids = stored_pair(run)
    folder = run / "data" / "scans" / ids["deep"]
    document = ScanDocument.model_validate_json((folder / "scan.json").read_bytes())
    live_review.save(
        folder,
        "scan.json",
        document.model_copy(update={"state": "running", "phase": "analysis"}).model_dump(
            mode="json"
        ),
    )
    before = live_review.hashes(run)
    monkeypatch.setattr(live_review, "ROOT", tmp_path)
    monkeypatch.setattr(
        live_review, "load_config", lambda: pytest.fail("No backend or network work")
    )
    monkeypatch.setattr(sys, "argv", ["live_review.py", "--verify-saved", "--artifacts", str(run)])
    with pytest.raises(SystemExit) as error:
        live_review.main()
    assert error.value.code == 2
    assert not list(run.glob("verification-*"))
    assert live_review.hashes(run) == before
