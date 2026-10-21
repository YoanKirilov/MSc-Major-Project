"""Trust hashes and tri-state source freshness; no downloads or installations."""

import hashlib
import io
import json

import pytest
from scripts import bootstrap_trust as trust
from scripts import live_review


def test_bootstrap_verifies_before_installing_and_never_uses_an_index(tmp_path, monkeypatch):
    payload = b"synthetic wheel bytes"
    monkeypatch.setattr(
        trust,
        "WHEELS",
        (
            (
                "synthetic.whl",
                "https://files.pythonhosted.org/synthetic",
                hashlib.sha256(payload).hexdigest(),
            ),
        ),
    )
    wheel = tmp_path / "synthetic.whl"
    wheel.write_bytes(payload)
    calls = []
    monkeypatch.setattr(
        trust.subprocess, "run", lambda command, **kwargs: calls.append((command, kwargs))
    )
    trust.bootstrap_trust("synthetic-python", tmp_path, offline=True)
    install = calls[0][0]
    assert all(flag in install for flag in ("-I", "--isolated", "--no-index", "--no-deps"))
    assert all(call[1]["timeout"] <= 120 for call in calls)
    assert str(wheel) in install and not any(part.startswith("https:") for part in install)
    calls.clear()
    wheel.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="verification failed"):
        trust.bootstrap_trust("synthetic-python", tmp_path, offline=True)
    assert not calls
    wheel.unlink()
    with pytest.raises(ValueError, match="Offline bootstrap requires"):
        trust.verified_wheels(tmp_path, offline=True)
    for destination in ("http://files.pythonhosted.org/wheel", "https://evil.example/wheel"):
        with pytest.raises(ValueError, match="redirect"):
            trust._HttpsOnly().redirect_request(None, None, 302, "", {}, destination)


@pytest.mark.parametrize(
    "running,expected,match,restart",
    [
        ("a" * 20, "a" * 20, True, False),
        ("b" * 20, "a" * 20, False, True),
        (None, "a" * 20, None, None),
        ("a" * 20, None, None, None),
    ],
)
def test_public_preflight_checks_actual_build_not_contract_alone(
    tmp_path, monkeypatch, running, expected, match, restart
):
    schema = {
        "paths": {},
        "components": {
            "schemas": {"CveLookupRequest": {"properties": {"operation_id": {"type": "string"}}}}
        },
    }
    (tmp_path / "app").mkdir()
    monkeypatch.setattr(live_review, "ROOT", tmp_path)

    def build(_):
        if expected is None:
            raise OSError("Synthetic unreadable source")
        return expected

    monkeypatch.setattr(live_review, "source_build_id", build)

    class Reply(io.BytesIO):
        headers = {
            "X-NetGuard-Contract": str(live_review.API_CONTRACT_VERSION),
            "X-NetGuard-Build": running,
        }

    monkeypatch.setattr(
        live_review.urllib.request,
        "urlopen",
        lambda url, **_: Reply(
            json.dumps(schema).encode() if url.endswith("openapi.json") else b""
        ),
    )
    value = live_review.normal_public_check(tmp_path)
    assert value["source_match"] is match and value["restart_required"] is restart
    assert value["expected_build"] == expected
