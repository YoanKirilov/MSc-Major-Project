from pathlib import Path

import pytest
from scripts.check_security import audit_covers, audit_requirements


def roots(tmp_path, development, security="tool==2.0\n"):
    (tmp_path / "requirements-dev.lock").write_text(development, encoding="utf-8")
    (tmp_path / "requirements-security.lock").write_text(security, encoding="utf-8")


def test_audit_flattens_nested_locks_with_markers_and_deduplication(tmp_path):
    roots(tmp_path, "-r runtime.lock\n-r build.lock\ntest==1.0\n")
    (tmp_path / "runtime.lock").write_text("runtime==1.0\n-r client.lock\n", encoding="utf-8")
    (tmp_path / "client.lock").write_text("client==1.0\n", encoding="utf-8")
    (tmp_path / "build.lock").write_text(
        "# Comment\nbackend==1.0\nclient==1.0\nplatform==1.0; sys_platform == 'win32'\n",
        encoding="utf-8",
    )
    lines = audit_requirements(tmp_path)
    assert lines == [
        "backend==1.0",
        "client==1.0",
        'platform==1.0; sys_platform == "win32"',
        "runtime==1.0",
        "test==1.0",
    ]
    assert not any(line.startswith("-r") for line in lines)


@pytest.mark.parametrize(
    "line", ["tool>=1.0", "tool==1.*", "--index-url https://example.invalid", "tool==3.0"]
)
def test_audit_rejects_unpinned_options_and_conflicts(tmp_path, line):
    roots(tmp_path, line + "\ntool==2.0")
    with pytest.raises(ValueError):
        audit_requirements(tmp_path)


def test_audit_rejects_outside_include_before_reading_it(tmp_path):
    roots(tmp_path, "-r ../private.lock")
    with pytest.raises(ValueError, match="inside the project"):
        audit_requirements(tmp_path)


def test_project_audit_includes_runtime_build_client_and_separate_security_pins():
    root = Path(__file__).resolve().parents[2]
    lines = audit_requirements(root)
    for pin in ("fastapi==", "setuptools==", "wheel==", "httpx2==", "pytest=="):
        assert any(line.startswith(pin) for line in lines), pin
    tools = audit_requirements(root, "requirements-security.lock")
    assert any(line.startswith("pip_audit==") for line in tools)
    assert "filelock==3.32.7" in lines and "filelock==4.0.5" in tools


def test_coverage_rejects_missing_or_skipped_packages():
    requirements = ["first==1.0", "second==2.0"]
    one = {"name": "first", "version": "1.0"}
    assert not audit_covers(requirements, {"dependencies": [one]})
    assert not audit_covers(
        requirements, {"dependencies": [one, {"name": "second", "skip_reason": "not audited"}]}
    )
    assert audit_covers(requirements, {"dependencies": [one, {"name": "second", "version": "2.0"}]})
    assert not audit_covers(requirements, {})
    assert not audit_covers(requirements, {"dependencies": None})
