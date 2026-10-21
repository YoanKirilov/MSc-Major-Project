"""Boundaries for audit improvements; synthetic data and in-memory transports only."""

from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from app.scanner.cve import _reference, _related_to_product
from app.schemas.advisory import CveAdvisory
from app.storage.backup import storage_usage
from tests.fixtures.diagnostics import redact, safe_trace


@pytest.mark.parametrize(
    "url",
    [
        "http://vendor.example/advice",
        "https://127.0.0.1/private",
        "https://192.168.1.1/",
        "https://[::1]/",
        "https://router.local/",
        # Deliberately fake credentials: the URL must be rejected, never fetched.
        "https://user:password@vendor.example/",  # pragma: allowlist secret
        "https://vendor.example:8443/",
        "https://vendor.example/#token=bad",
        "javascript:alert(1)",
        "https://vendor.example/\nprivate",
        "https://2130706433/",
    ],
)
def test_advisory_urls_reject_unsafe_destinations(url):
    with pytest.raises(ValueError):
        CveAdvisory(url=url)


def test_advisories_are_bounded_deduplicated_nvd_tagged_and_not_inferred():
    record = _reference(
        {
            "id": "CVE-2026-10001",
            "descriptions": [],
            "references": [
                {"url": "https://vendor.example/advice", "tags": ["Vendor Advisory"]},
                {"url": "https://vendor.example/advice", "tags": ["Vendor Advisory"]},
                {"url": "https://127.0.0.1/", "tags": ["Vendor Advisory"]},
                {"url": "https://unrelated.example/", "tags": ["Exploit"]},
                {"url": "https://invalid.example/", "tags": None},
            ],
        }
    )
    assert [item.url for item in record.advisories] == ["https://vendor.example/advice"]
    assert not _related_to_product(
        {"affected": [{"product": "Example"}]}, "cpe:2.3:a:x:y:*:*:*:*:*:*:*:*"
    )


def test_safe_trace_redacts_session_values_without_extracting_files(tmp_path):
    source, target = tmp_path / "private.zip", tmp_path / "safe.zip"
    secrets = {"synthetic-bootstrap-secret", "synthetic-csrf-secret"}
    with ZipFile(source, "w") as archive:
        archive.writestr("trace.trace", '{"url":"/#token=synthetic-bootstrap-secret"}')
        archive.writestr("resources/session.json", '{"csrf_token":"synthetic-csrf-secret"}')
    assert safe_trace(source, target, secrets)
    with ZipFile(target) as archive:
        values = b"".join(archive.read(name) for name in archive.namelist())
        assert b"[redacted]" in values
        assert not any(value.encode() in values for value in secrets)
    assert redact("error synthetic-csrf-secret", secrets) == "error [redacted]"


def test_recovery_capacity_warns_by_count_without_deleting(tmp_path, monkeypatch):
    from app.storage import backup

    fake = [(f".trash/{index}/.removal-receipt.json", None, 1) for index in range(800)]
    monkeypatch.setattr(backup, "files_to_backup", lambda _: (fake, 800))
    value = storage_usage(tmp_path)
    assert value["recovery_reports"] == 800
    assert value["recovery_near_limit"]
    assert "does not free space" in value["warning"]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("browser_only", [False, True])
def test_check_runner_separates_offline_and_selected_browser_jobs(
    tmp_path, monkeypatch, browser_only
):
    from scripts import check

    (tmp_path / "app/static/js").mkdir(parents=True)
    monkeypatch.setattr(check, "__file__", str(tmp_path / "scripts" / "check.py"))
    monkeypatch.setattr(check.shutil, "which", lambda _: "node")
    monkeypatch.setenv("RUN_LIVE_OLLAMA", "1")
    monkeypatch.setenv("RUN_BROWSER_TESTS", "1")
    arguments = ["check.py", "--ci-artifacts"]
    if browser_only:
        arguments += ["--browser-only", "--browser-engines", "firefox"]
    monkeypatch.setattr(check.sys, "argv", arguments)
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(check.subprocess, "run", run)
    assert check.main() == 0
    pytest_calls = [(command, kwargs) for command, kwargs in calls if "pytest" in command]
    assert len(pytest_calls) == 1
    command, kwargs = pytest_calls[0]
    selection = command[command.index("pytest") + 2]
    assert "not live_lab" in selection and "not live_provider" in selection
    assert (" and browser" in selection) == browser_only
    assert ("not browser" in selection) != browser_only
    assert kwargs["env"]["RUN_LIVE_OLLAMA"] == "0"
    assert kwargs["env"]["RUN_BROWSER_TESTS"] == ("1" if browser_only else "0")
    assert kwargs["env"]["RESPONSIVE_BROWSERS"] == ("firefox" if browser_only else "chromium")
    assert "ci-reports" in kwargs["env"]["NETGUARD_DIAGNOSTICS_DIR"]
    assert (len(calls) == 1) == browser_only
