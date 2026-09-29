import json
from types import SimpleNamespace

import pytest
from scripts import check_security


@pytest.mark.parametrize(
    "audit_code,severity,secrets,expected",
    [
        (0, "LOW", {}, 0),
        (1, "LOW", {}, 1),
        (0, "MEDIUM", {}, 1),
        (0, "HIGH", {}, 1),
        (0, "LOW", {"example.py": [{"type": "synthetic"}]}, 1),
    ],
)
def test_security_gate_fails_closed(tmp_path, monkeypatch, audit_code, severity, secrets, expected):
    monkeypatch.setattr(check_security, "__file__", str(tmp_path / "scripts/check_security.py"))
    monkeypatch.setattr(check_security.subprocess, "check_output", lambda *a, **kw: b"")

    def run(args, **kwargs):
        if "pip_audit" in args:
            return SimpleNamespace(returncode=audit_code)
        if "bandit" in args:
            from pathlib import Path

            Path(args[args.index("-o") + 1]).write_text(
                json.dumps(
                    {
                        "results": [{"issue_severity": severity}],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=1)
        assert "--no-verify" in args
        return SimpleNamespace(returncode=0, stdout=json.dumps({"results": secrets}))

    monkeypatch.setattr(check_security.subprocess, "run", run)
    assert check_security.main() == expected
