"""Sharing checks use synthetic documents only and never start an app scanner."""

import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.api.report_export import (
    MAX_PRIVATE_TOKEN_CHARS,
    MAX_PRIVATE_TOKENS,
    PrivatePreviewTooLarge,
    build_share_report,
    router,
)
from app.explanations.service import PROMPT_VERSION
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import ReportAnnotations
from app.storage.json_store import JsonStore
from app.storage.nicknames import NicknameDocument
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL

CREATED = "2026-10-14T09:15:00Z"
FINISHED = "2026-10-14T09:16:00Z"


def synthetic_report(**updates):
    scan_id, device_id, service_id, finding_id = [str(uuid4()) for _ in range(4)]
    fixed = {
        "meaning": "Kitchen-Laptop at 192.168.56.10 answered a selected check.",
        "why_it_matters": "Review the observed feature before changing settings.",
        "recommended_steps": ["Check Kitchen-Laptop at 192.168.56.10."],
        "how_to_check": ["Review the saved observation."],
    }
    data = dict(
        scan_id=scan_id,
        created_at=CREATED,
        started_at=CREATED,
        finished_at=FINISHED,
        phase="finished",
        state="partial",
        scan_outcome="partial",
        analysis_status="ready",
        target={"mode": "known_hosts", "hosts": ["192.168.56.10", "192.168.56.11"]},
        policy={
            "profile": "deep-tcp-v1",
            "tcp_ports": ["all-tcp"],
            "udp_ports": [53, 161],
            "allowed_network": "192.168.56.0/24",
            "network_context": {"private": "NEVER_EXPORT_CONTEXT"},
        },
        coverage={
            "candidate_count": 2,
            "service_attempted_count": 2,
            "service_completed_count": 1,
            "service_failed_count": 1,
            "targets": [
                {"ip": "192.168.56.10", "service_status": "completed"},
                {
                    "ip": "192.168.56.11",
                    "service_status": "timed_out",
                    "reason_code": "host_scan_timeout",
                },
            ],
        },
        devices=[
            {
                "device_id": device_id,
                "scan_id": scan_id,
                "ip": "192.168.56.10",
                "hostname": "Kitchen-Laptop",
                "mac": "02:00:00:00:00:10",
                "observed_at": CREATED,
                "host_script_results": [
                    {"script_id": "smb-os-discovery", "output": "NEVER_EXPORT_HOST_SCRIPT"}
                ],
            }
        ],
        services=[
            {
                "service_id": service_id,
                "device_id": device_id,
                "port": 80,
                "state": "open",
                "name": "http",
                "product": "NEVER_EXPORT_BANNER",
                "extra_info": "NEVER_EXPORT_EXTRA_INFO",
                "script_results": [{"script_id": "http-title", "output": "NEVER_EXPORT_WEB_TITLE"}],
                "observed_at": CREATED,
            }
        ],
        findings=[
            {
                "finding_id": finding_id,
                "device_id": device_id,
                "service_id": service_id,
                "rule_id": "R01",
                "rule_version": "1.0.0",
                "title": "Original reviewed title",
                "severity": "high",
                "confidence": "medium",
                "evidence": [{"field": "private", "value": "NEVER_EXPORT_RAW_EVIDENCE"}],
                "limitations": ["Only selected checks were run for Kitchen-Laptop."],
                "fixed_explanation": fixed,
                "actions": [
                    {
                        "action_id": "review",
                        "text": fixed["recommended_steps"][0],
                        "verification": fixed["how_to_check"][0],
                    }
                ],
                "created_at": CREATED,
            }
        ],
        explanations=[
            {
                "finding_id": finding_id,
                "status": "ready",
                "source": "ai",
                "provider": "ollama",
                "model": "synthetic-model",
                "prompt_version": PROMPT_VERSION,
                "content": {
                    **fixed,
                    "meaning": "Accepted wording for Kitchen-Laptop at 192.168.56.10.",
                },
                "display_title": "Accepted reviewed title",
                "ai_fields": ["title", "meaning"],
                "completed_at": FINISHED,
            }
        ],
        warnings=[
            {
                "code": "SYNTHETIC",
                "message": "Kitchen-Laptop 02:00:00:00:00:10; "
                "http://unknown-house.local/a; 10.55.1.9; fe80::1234.",
            }
        ],
        errors=[{"code": "HOST_SCAN_TIMEOUT", "message": "192.168.56.11 did not finish."}],
    )
    data.update(updates)
    return ScanDocument(**data)


def annotations(document):
    return ReportAnnotations(
        title="Mum's study report for Kitchen-Laptop",
        action_checks=[
            {
                "finding_id": document.findings[0].finding_id,
                "action_id": "review",
                "status": "checked",
                "updated_at": FINISHED,
            }
        ],
        name_refreshes=[
            {
                "device_id": document.devices[0].device_id,
                "checked_at": FINISHED,
                "names": [{"name": "Kitchen-Printer", "source": "synthetic"}],
                "notes": ["Personal note for Kitchen-Printer at 192.168.56.10."],
            }
        ],
    )


def test_default_projection_removes_identifiers_and_raw_data_from_every_prose_field():
    document = synthetic_report()
    result = build_share_report(
        document,
        annotations=annotations(document),
        names={document.devices[0].device_id: "Mum's study"},
    )
    encoded = json.dumps(result)
    for private in [
        "192.168.56",
        "10.55.1.9",
        "fe80::1234",
        "02:00:00:00:00:10",
        "Kitchen-Laptop",
        "Kitchen-Printer",
        "Mum's study",
        "unknown-house.local",
        "NEVER_EXPORT",
        document.scan_id,
    ]:
        assert private not in encoded
    assert "identifiers" not in result["devices"][0]
    assert "notes" not in result
    assert result["title"] == "Deep scan report"
    assert "not a guarantee of anonymity" in result["privacy"]["notice"]
    assert result["findings"][0]["content"]["meaning"].startswith("Accepted wording")
    assert result["findings"][0]["fixed_explanation"]["meaning"].endswith(
        "answered a selected check."
    )


def test_scope_dates_partial_coverage_original_priority_and_review_provenance_survive_export():
    document = synthetic_report()
    result = build_share_report(document, annotations=annotations(document))
    assert result["created_at"] == CREATED
    assert result["finished_at"] == FINISHED
    assert result["state"] == "partial"
    assert result["scope"] == {"mode": "selected", "tcp_ports": ["all-tcp"], "udp_ports": [53, 161]}
    assert result["coverage"]["service_completed_count"] == 1
    assert result["coverage"]["unfinished_device_count"] == 1
    assert result["coverage"]["targets"][1]["reason_code"] == "host_scan_timeout"
    assert result["findings"][0]["severity"] == "high"
    assert result["findings"][0]["confidence"] == "medium"
    assert result["findings"][0]["actions"][0]["review_status"] == "checked"
    assert "does not confirm a fix" in result["review_status_note"]
    assert result["findings"][0]["provenance"]["ai_fields"] == ["title", "meaning"]
    assert result["findings"][0]["provenance"]["model"] == "synthetic-model"
    assert result["findings"][0]["title"] == "Accepted reviewed title"
    assert result["findings"][0]["fixed_title"] == "Original reviewed title"


def test_optional_identifiers_and_notes_are_independent_and_banners_stay_excluded():
    document = synthetic_report()
    notes = annotations(document)
    named = build_share_report(document, include_identifiers=True, annotations=notes)
    assert named["devices"][0]["identifiers"]["hostname"] == "Kitchen-Laptop"
    assert "192.168.56.10" in named["findings"][0]["content"]["meaning"]
    assert "notes" not in named
    private_notes = build_share_report(document, include_notes=True, annotations=notes)
    assert "Kitchen-Printer" not in json.dumps(private_notes)
    assert "192.168.56.10" not in json.dumps(private_notes)
    full = build_share_report(
        document, include_notes=True, include_identifiers=True, annotations=notes
    )
    assert full["notes"]["title"] == notes.title
    assert full["notes"]["identification_notes"][0]["notes"] == notes.name_refreshes[0].notes
    assert "NEVER_EXPORT" not in json.dumps(full)


def test_stale_ai_wording_is_hidden_and_failed_notes_never_become_unchecked_claims():
    document = synthetic_report()
    document.explanations[0].prompt_version = "older-version"
    result = build_share_report(document, annotations=annotations(document), notes_available=False)
    finding = result["findings"][0]
    assert "Accepted wording" not in finding["content"]["meaning"]
    assert finding["provenance"]["source"] == "reviewed_guidance"
    assert finding["provenance"]["older_ai_wording_hidden"] is True
    assert finding["actions"][0]["review_status"] == "unavailable"
    assert finding["actions"][0]["review_updated_at"] is None
    assert result["annotations_available"] is False


def test_unrecorded_port_selection_and_empty_results_are_not_invented_as_security_success():
    result = build_share_report(
        synthetic_report(policy={}, devices=[], services=[], findings=[], explanations=[])
    )
    assert result["scope"]["tcp_ports"] == []
    assert result["scope"]["udp_ports"] == []
    assert result["findings"] == []
    assert result["coverage"]["unfinished_device_count"] == 1
    assert "could not finish" in result["overview"]["limitations"][0]


def test_private_identifier_budget_is_bounded_and_never_silently_drops_redactions():
    document = synthetic_report()
    too_many = {
        str(index): f"Synthetic household name {index}" for index in range(MAX_PRIVATE_TOKENS)
    }
    with pytest.raises(PrivatePreviewTooLarge):
        build_share_report(document, names=too_many)
    with pytest.raises(PrivatePreviewTooLarge):
        build_share_report(document, names={"synthetic": "s" * (MAX_PRIVATE_TOKEN_CHARS + 1)})
    assert build_share_report(document, names=too_many, include_identifiers=True)["devices"]


def test_discovery_export_lists_observed_and_unfinished_checks_without_254_empty_rows():
    targets = [
        {
            "ip": f"192.168.56.{index}",
            "discovery_status": "not_seen",
            "service_status": "skipped" if index % 2 else "not_scheduled",
        }
        for index in range(1, 255)
    ]
    targets[9] = {
        "ip": "192.168.56.10",
        "discovery_status": "observed",
        "service_status": "completed",
    }
    targets[10] = {
        "ip": "192.168.56.11",
        "discovery_status": "observed",
        "service_status": "timed_out",
        "reason_code": "host_scan_timeout",
    }
    document = synthetic_report(
        target={"mode": "discover", "cidr": "192.168.56.0/24", "hosts": []},
        coverage={
            "candidate_count": 254,
            "discovered_count": 2,
            "service_attempted_count": 2,
            "service_completed_count": 1,
            "service_failed_count": 1,
            "service_skipped_count": 126,
            "discovery_complete": True,
            "service_stage_complete": False,
            "targets": targets,
        },
    )
    result = build_share_report(document, include_identifiers=True)
    coverage = result["coverage"]
    assert len(coverage["targets"]) == 2
    assert [target["ip"] for target in coverage["targets"]] == ["192.168.56.10", "192.168.56.11"]
    assert coverage["targets"][1]["service_status"] == "timed_out"
    assert coverage["targets"][1]["reason_code"] == "host_scan_timeout"
    assert coverage["candidate_count"] == 254
    assert coverage["discovered_count"] == 2
    assert coverage["service_attempted_count"] == 2
    assert coverage["service_completed_count"] == 1
    assert coverage["service_failed_count"] == 1
    assert coverage["service_skipped_count"] == 126
    assert coverage["unfinished_device_count"] == 1
    assert coverage["unlisted_target_count"] == 252
    assert coverage["unlisted_not_observed_count"] == 252
    assert coverage["unlisted_skipped_count"] == 126
    assert coverage["unlisted_not_scheduled_count"] == 126
    assert len(coverage["targets"]) + coverage["unlisted_target_count"] == len(targets)
    assert "Some checks could not finish" in result["overview"]["limitations"][0]


def test_known_host_export_keeps_selected_unfinished_hosts_and_omits_unselected_ledger_rows():
    document = synthetic_report()
    document.coverage.targets.append(
        document.coverage.targets[0].model_copy(
            update={"ip": "192.168.56.200", "service_status": "not_scheduled"}
        )
    )
    coverage = build_share_report(document, include_identifiers=True)["coverage"]
    assert [target["ip"] for target in coverage["targets"]] == ["192.168.56.10", "192.168.56.11"]
    assert coverage["targets"][1]["service_status"] == "timed_out"
    assert coverage["unlisted_target_count"] == 1
    assert coverage["unlisted_not_scheduled_count"] == 1
    assert coverage["unfinished_device_count"] == document.unfinished_device_count


@pytest.fixture
def export_client(tmp_path):
    store = JsonStore(tmp_path)
    document = synthetic_report()
    store._create_scan(document)
    note_path = store._scan_dir(document.scan_id) / "annotations.json"
    store._atomic_write(note_path, annotations(document).model_dump_json())
    nicknames = NicknameDocument(
        entries=[
            {
                "scan_id": document.scan_id,
                "device_id": document.devices[0].device_id,
                "nickname": "Mum's study",
            }
        ]
    )
    store._atomic_write(tmp_path / "nicknames.json", nicknames.model_dump_json())
    app = FastAPI()
    app.include_router(router)
    manager = SessionManager()
    app.state.store = store
    app.state.config = SimpleNamespace(port=8765)
    app.state.session_manager = manager
    with TestClient(app, base_url=BASE_URL) as client:
        yield client, manager, store, document


def sign_in(client, manager):
    client.cookies.set("session_id", manager.register_session())


def test_share_route_requires_session_and_returns_no_store_projection(export_client):
    client, manager, _, document = export_client
    path = f"/api/live-scans/{document.scan_id}/share"
    assert client.get(path).status_code == 401
    sign_in(client, manager)
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "192.168.56.10" not in response.text
    assert response.json()["schema_version"] == 1
    assert client.get(path, headers={"Host": "untrusted.example"}).status_code == 403


@pytest.mark.parametrize("parameter", ["include_identifiers", "include_notes"])
@pytest.mark.parametrize("value", ["yes", "1", "0", "True", "FALSE", "", "null"])
def test_privacy_query_requires_explicit_lowercase_boolean_values(export_client, parameter, value):
    client, manager, _, document = export_client
    sign_in(client, manager)
    response = client.get(f"/api/live-scans/{document.scan_id}/share", params={parameter: value})
    assert response.status_code == 422


def test_valid_optional_flags_and_read_only_sidecar_failures(export_client):
    client, manager, store, document = export_client
    sign_in(client, manager)
    path = f"/api/live-scans/{document.scan_id}/share"
    response = client.get(path, params={"include_identifiers": "true", "include_notes": "true"})
    assert response.status_code == 200
    assert response.json()["devices"][0]["identifiers"]["nickname"] == "Mum's study"
    note_path = store._scan_dir(document.scan_id) / "annotations.json"
    store._atomic_write(
        note_path.with_name("annotations.previous.json"), annotations(document).model_dump_json()
    )
    store._atomic_write(note_path, "{broken")
    before = {str(item): item.read_bytes() for item in store.data_root.rglob("*") if item.is_file()}
    exported = client.get(path).json()
    after = {str(item): item.read_bytes() for item in store.data_root.rglob("*") if item.is_file()}
    assert before == after
    assert exported["annotations_available"] is False
    assert exported["findings"][0]["actions"][0]["review_status"] == "unavailable"


def test_running_demo_missing_and_unreadable_reports_have_specific_boundaries(export_client):
    client, manager, store, document = export_client
    sign_in(client, manager)
    missing = f"/api/live-scans/{uuid4()}/share"
    assert client.get(missing).status_code == 404
    assert client.get("/api/live-scans/not-an-id/share").status_code == 404
    running = synthetic_report(phase="analysis", state="running")
    store._create_scan(running)
    assert client.get(f"/api/live-scans/{running.scan_id}/share").status_code == 409
    demo = synthetic_report(source="demo")
    store._create_scan(demo)
    assert client.get(f"/api/live-scans/{demo.scan_id}/share").status_code == 404
    store._atomic_write(store._scan_dir(document.scan_id) / "scan.json", "{unreadable")
    assert client.get(f"/api/live-scans/{document.scan_id}/share").status_code == 404
