import asyncio
import json
from copy import deepcopy
from html import escape
from uuid import uuid4

import pytest
from app.explanations.presentation import plain_finding
from app.explanations.service import PROMPT_VERSION, ExplanationService, build_safe_findings
from app.explanations.validation import validated_line
from app.explanations.wording import wording_choices
from app.jobs.supervisor import ScanSupervisor
from app.main import create_app
from app.profiling.history import compare_history
from app.risk.catalogue import RULE_CATALOGUE, RULESET_VERSION
from app.risk.engine import evaluate_device
from app.risk.guidance import guidance_status, refresh_guidance
from app.risk.smb import parse_protocols, parse_signing
from app.scanner.commands import (
    CONFIGURATION_CHECKS_VERSION,
    DEEP_PROFILE,
    DEEP_PROFILE_ID,
    DEEP_SAFE_SCRIPTS,
    DEEP_UDP_PORTS,
    LIGHT_SAFE_SCRIPTS,
    PROFILE_ID,
    host_command,
)
from app.scanner.parser import parse_host
from app.scanner.runner import ProcessResult
from app.schemas.scan import Device, ScanDocument, ScriptEvidence, Service
from app.schemas.settings import Settings
from app.security.session import SessionManager
from app.storage.json_store import JsonStore
from fastapi.testclient import TestClient
from tests.fixtures.provider import ReviewedProvider
from tests.session_helpers import BASE_URL, authenticate_client

PROTOCOLS = "\n  dialects:\n    NT LM 0.12 (SMBv1) [dangerous, but default]\n    3.1.1\n"
OPTIONAL_SIGNING = "\n  3.1.1:\n    Message signing enabled but not required\n"
REQUIRED_SIGNING = "\n  3.1.1:\n    Message signing enabled and required\n"


def evidence(script_id, output, *, truncated=False):
    return ScriptEvidence(script_id=script_id, output=output, truncated=truncated)


def fixtures(*, origin="host", protocols=PROTOCOLS, signing=OPTIONAL_SIGNING, port=445):
    scan_id, device_id = str(uuid4()), str(uuid4())
    scripts = []
    if protocols is not None:
        scripts.append(evidence("smb-protocols", protocols))
    if signing is not None:
        scripts.append(evidence("smb2-security-mode", signing))
    device = Device(
        scan_id=scan_id,
        device_id=device_id,
        ip="192.168.56.10",
        mac="aa:bb:cc:dd:ee:02",
        hostname="PRIVATE_SMB_NAME",
        observed_at="2026-10-14T10:00:00Z",
        host_script_results=scripts if origin == "host" else [],
    )
    service = Service(
        service_id=str(uuid4()),
        device_id=device_id,
        protocol="tcp",
        port=port,
        state="open",
        name="microsoft-ds",
        detection_method="probed",
        nmap_confidence=10,
        observed_at=device.observed_at,
        script_results=scripts if origin == "port" else [],
    )
    return device, [service]


def configuration_findings(device, services, *, profile=DEEP_PROFILE):
    return [
        finding
        for finding in evaluate_device(device, services, profile=profile)
        if finding.rule_id in {"R08", "R09"}
    ]


@pytest.mark.parametrize("origin", ["host", "port"])
def test_positive_smb_configuration_facts_are_bound_to_endpoint_and_stable(origin):
    device, services = fixtures(origin=origin)
    findings = configuration_findings(device, services)
    assert [finding.rule_id for finding in findings] == ["R08", "R09"]
    assert [finding.severity for finding in findings] == ["high", "medium"]
    assert all(finding.confidence == "medium" for finding in findings)
    assert [finding.finding_id for finding in configuration_findings(device, services)] == [
        finding.finding_id for finding in findings
    ]
    assert all(finding.service_id == services[0].service_id for finding in findings)
    facts = {item.field: item.value for item in findings[1].evidence}
    assert facts["port"] == 445 and facts["protocol"] == "tcp"
    assert facts["script_scope"] == origin
    assert facts["negotiated_smb_version"] == "3.1.1"
    assert facts["message_signing_required"] is False
    assert "negotiated" in findings[1].fixed_explanation.meaning
    assert any("other versions" in line for line in findings[1].limitations)


@pytest.mark.parametrize("profile", [None, "light", "other"])
def test_configuration_findings_are_deep_only(profile):
    device, services = fixtures()
    assert not configuration_findings(device, services, profile=profile)
    assert evaluate_device(device, services, profile=profile)[0].rule_id == "R05"


def test_host_scripts_use_documented_tcp445_precedence_when_both_ports_are_open():
    device, services = fixtures()
    alternate = services[0].model_copy(update={"port": 139, "service_id": str(uuid4())})
    services.append(alternate)
    findings = configuration_findings(device, services)
    assert len(findings) == 2
    assert all(finding.service_id == services[0].service_id for finding in findings)
    assert all(
        next(item.value for item in finding.evidence if item.field == "port") == 445
        for finding in findings
    )


@pytest.mark.parametrize(
    "udp_state,allowed",
    [
        (None, True),
        ("unknown", True),
        ("open", True),
        ("open_filtered", True),
        ("closed", False),
        ("filtered", False),
    ],
)
def test_host_tcp139_fallback_matches_nmap_netbios_selection(udp_state, allowed):
    device, services = fixtures(port=139)
    if udp_state is not None:
        services.append(
            services[0].model_copy(
                update={
                    "service_id": str(uuid4()),
                    "port": 137,
                    "protocol": "udp",
                    "state": udp_state,
                }
            )
        )
    assert bool(configuration_findings(device, services)) is allowed


@pytest.mark.parametrize(
    "change",
    [
        {"state": "closed"},
        {"state": "open_filtered"},
        {"protocol": "udp"},
        {"port": 8445},
        {"tunnel": "ssl"},
        {"device_id": "different-device"},
    ],
)
def test_configuration_output_cannot_be_attached_to_unrelated_connection(change):
    device, services = fixtures()
    services[0] = services[0].model_copy(update=change)
    assert not configuration_findings(device, services)


def test_negotiation_evidence_is_not_inferred_from_name_or_port():
    device, services = fixtures(protocols=None, signing=None)
    assert not configuration_findings(device, services)
    # Conversely, a successful checked negotiation is stronger than a port-name table.
    device, services = fixtures()
    services[0].detection_method = "table"
    services[0].name = None
    services[0].nmap_confidence = None
    assert {finding.rule_id for finding in configuration_findings(device, services)} == {
        "R08",
        "R09",
    }


@pytest.mark.parametrize(
    "output",
    [
        "SMBv1 is disabled",
        "ERROR: SMBv1 could not be checked",
        "",
        PROTOCOLS + "unknown dialect\n",
        "dialects:\nNT LM 0.12 (SMBv1)\nNT LM 0.12",
        "dialects:\nNT LM 0.12\n2.9",
        "dialects:\n2.0.2\n3.1.1",
        "dialects:\nNT LM 0.12\n" + " " * 1024,
    ],
)
def test_smb1_requires_complete_unambiguous_positive_dialect_list(output):
    device, services = fixtures(protocols=output, signing=None)
    assert not configuration_findings(device, services)


@pytest.mark.parametrize(
    "output,expected",
    [
        (OPTIONAL_SIGNING, True),
        ("2.0.2:\nMessage signing is disabled and not required!", True),
        (REQUIRED_SIGNING, False),
        ("3.1.1:\nMessage signing is disabled!", False),
        ("3.1.1:\nMessage signing not required", False),
        ("Message signing enabled but not required", False),
        ("3.1.1:\nMessage signing enabled but not required\nERROR", False),
        (OPTIONAL_SIGNING + REQUIRED_SIGNING, False),
        ("4.0:\nMessage signing enabled but not required", False),
        ("Couldn't establish a SMBv2 connection.", False),
    ],
)
def test_signing_not_required_is_version_bound_exact_fact(output, expected):
    device, services = fixtures(protocols=None, signing=output)
    assert bool(configuration_findings(device, services)) is expected


@pytest.mark.parametrize("script_id", ["smb-protocols", "smb2-security-mode"])
def test_truncated_or_duplicate_script_output_produces_no_configuration_finding(script_id):
    device, services = fixtures()
    target = next(script for script in device.host_script_results if script.script_id == script_id)
    target.truncated = True
    findings = configuration_findings(device, services)
    assert not any(
        item.rule_id == ("R08" if script_id == "smb-protocols" else "R09") for item in findings
    )
    target.truncated = False
    device.host_script_results.append(target.model_copy())
    findings = configuration_findings(device, services)
    assert not any(
        item.rule_id == ("R08" if script_id == "smb-protocols" else "R09") for item in findings
    )


def test_conflicting_host_and_port_evidence_is_rejected_but_agreement_is_not_duplicated():
    device, services = fixtures(protocols=None)
    services[0].script_results = [evidence("smb2-security-mode", REQUIRED_SIGNING)]
    assert not configuration_findings(device, services)
    services[0].script_results = [evidence("smb2-security-mode", OPTIONAL_SIGNING)]
    result = configuration_findings(device, services)
    assert len(result) == 1
    assert next(item.value for item in result[0].evidence if item.field == "script_scope") == (
        "host and port"
    )


def test_ambiguous_duplicate_ports_and_service_identifiers_are_rejected():
    device, services = fixtures()
    services.append(services[0].model_copy(update={"service_id": str(uuid4())}))
    assert not configuration_findings(device, services)
    device, services = fixtures(origin="port")
    services.append(services[0].model_copy(update={"port": 139}))
    assert not configuration_findings(device, services)


def test_pure_parsers_preserve_input_and_reject_control_corruption():
    protocol = evidence("smb-protocols", PROTOCOLS)
    signing = evidence("smb2-security-mode", OPTIONAL_SIGNING)
    before = [protocol.model_dump(), signing.model_dump()]
    assert parse_protocols(protocol) == ("SMBv1", "3.1.1")
    assert parse_signing(signing) == ("3.1.1", "enabled", False)
    assert [protocol.model_dump(), signing.model_dump()] == before
    protocol.output = "dialects:\nNT LM 0.12\x00"
    assert parse_protocols(protocol) is None


def xml_result():
    scripts = "".join(
        f'<script id="{name}" output="{escape(output, quote=True).replace(chr(10), "&#10;")}"/>'
        for name, output in (("smb-protocols", PROTOCOLS), ("smb2-security-mode", OPTIONAL_SIGNING))
    )
    return (
        '<nmaprun><host><status state="up"/><address addrtype="ipv4" addr="192.168.56.10"/>'
        '<ports><port protocol="tcp" portid="445"><state state="open"/>'
        '<service name="microsoft-ds" method="probed" conf="10"/></port></ports>'
        f"<hostscript>{scripts}</hostscript></host>"
        '<runstats><finished exit="success"/></runstats></nmaprun>'
    ).encode()


def test_nmap_hostscript_parser_to_configuration_rules_replays_saved_evidence():
    device, services = parse_host(
        xml_result(),
        "192.168.56.10",
        str(uuid4()),
        profile_tcp_ports=range(1, 65536),
        profile_udp_ports=DEEP_UDP_PORTS,
        fill_unknown=False,
    )
    assert len(device.host_script_results) == 2
    assert not any(script.truncated for script in device.host_script_results)
    assert {finding.rule_id for finding in configuration_findings(device, services)} == {
        "R08",
        "R09",
    }


@pytest.mark.parametrize("profile", ["light", DEEP_PROFILE])
@pytest.mark.asyncio
async def test_supervisor_passes_profile_context_and_persists_configuration_facts(
    tmp_path,
    profile,
):
    store = JsonStore(tmp_path)
    document = ScanDocument(
        scan_id=str(uuid4()),
        target={"mode": "known_hosts", "hosts": ["192.168.56.10"]},
        policy={"profile": profile},
        coverage={"candidate_count": 1, "targets": [{"ip": "192.168.56.10"}]},
    )
    await store.create_scan(document)

    async def runner(*args):
        return ProcessResult(xml_result(), b"", 0, 0.01)

    await ScanSupervisor(store, process_runner=runner)._run(document.scan_id, asyncio.Event())
    saved = await store.load_scan(document.scan_id)
    assert saved.phase == "finished"
    assert len(saved.devices[0].host_script_results) == 2
    assert {finding.rule_id for finding in saved.findings if finding.rule_id in {"R08", "R09"}} == (
        {"R08", "R09"} if profile == DEEP_PROFILE else set()
    )


def test_deep_allowlist_is_fixed_and_light_coverage_is_unchanged():
    deep = host_command("synthetic-nmap", "192.168.56.10", DEEP_PROFILE)
    light = host_command("synthetic-nmap", "192.168.56.10", "light")
    assert deep[deep.index("--script") + 1] == DEEP_SAFE_SCRIPTS
    assert {"smb-protocols", "smb2-security-mode"}.issubset(set(DEEP_SAFE_SCRIPTS.split(",")))
    assert not {"smb-protocols", "smb2-security-mode"}.intersection(LIGHT_SAFE_SCRIPTS.split(","))
    assert light[light.index("--script") + 1] == LIGHT_SAFE_SCRIPTS
    assert deep[deep.index("--script-timeout") + 1] == "30s"
    assert deep[deep.index("--host-timeout") + 1] == "900s"
    assert "--script-args" not in deep
    assert DEEP_PROFILE == "deep-tcp-v1" and DEEP_PROFILE_ID != DEEP_PROFILE
    assert PROFILE_ID == "tcp12-udp3-v5"


@pytest.mark.parametrize("profile", ["light", DEEP_PROFILE])
def test_saved_api_policy_versions_deep_coverage_and_records_allowlist(monkeypatch, profile):
    async def settings():
        return Settings(allowed_network="192.168.56.0/24", mdns_enabled=False)

    async def no_job(*args, **kwargs):
        pass

    async def no_provider():
        return False

    monkeypatch.setattr("app.api.scans.nmap_preflight", lambda config: (True, "synthetic"))
    monkeypatch.setattr("app.api.scans.resolve_nmap_path", lambda config: "synthetic-nmap")
    manager = SessionManager()
    with TestClient(create_app(session_manager=manager), base_url=BASE_URL) as client:
        headers = authenticate_client(client, manager)
        monkeypatch.setattr(client.app.state.store, "load_settings", settings)
        monkeypatch.setattr(client.app.state.supervisor, "start", no_job)
        monkeypatch.setattr(client.app.state.explanations, "provider_available", no_provider)
        response = client.post(
            "/api/live-scans",
            headers=headers,
            json={
                "mode": "known_hosts",
                "hosts": ["192.168.56.10"],
                "profile": profile,
                "authorised": True,
            },
        )
        assert response.status_code == 202, response.text
        saved = client.portal.call(client.app.state.store.load_scan, response.json()["scan_id"])
        assert saved.policy["profile"] == profile
        assert saved.policy["profile_id"] == (
            DEEP_PROFILE_ID if profile == DEEP_PROFILE else PROFILE_ID
        )
        assert saved.policy["selected_scripts"] == (
            DEEP_SAFE_SCRIPTS if profile == DEEP_PROFILE else LIGHT_SAFE_SCRIPTS
        ).split(",")
        assert saved.policy["configuration_checks_version"] == (
            CONFIGURATION_CHECKS_VERSION if profile == DEEP_PROFILE else None
        )
        assert saved.versions["rules"] == RULESET_VERSION
        assert saved.versions["prompt"] == PROMPT_VERSION


def scan_document(device, services):
    return ScanDocument(
        scan_id=device.scan_id,
        created_at=device.observed_at,
        state="completed",
        phase="finished",
        target={"mode": "known_hosts", "hosts": [device.ip]},
        policy={
            "profile": DEEP_PROFILE,
            "profile_id": DEEP_PROFILE_ID,
            "allowed_network": "192.168.56.0/24",
            "tcp_ports": ["all-tcp"],
            "udp_ports": list(DEEP_UDP_PORTS),
        },
        devices=[device],
        services=services,
        findings=evaluate_device(device, services, profile=DEEP_PROFILE),
        coverage={
            "candidate_count": 1,
            "service_completed_count": 1,
            "targets": [{"ip": device.ip, "service_status": "completed"}],
        },
    )


def test_new_deep_coverage_never_compares_as_identical_to_older_deep():
    device, services = fixtures()
    current = scan_document(device, services)
    old_device, old_services = fixtures()
    previous = scan_document(old_device, old_services)
    previous.created_at = "2026-10-13T10:00:00Z"
    previous.policy["profile_id"] = DEEP_PROFILE
    compare_history(current, [previous])
    assert current.devices[0].comparison.status == "not_compared"
    assert "different profiles" in current.devices[0].comparison.reason


def test_guidance_refresh_preserves_configuration_identity_assessment_and_evidence():
    device, services = fixtures()
    document = scan_document(device, services)
    old = next(finding for finding in document.findings if finding.rule_id == "R08")
    old.rule_version = "0.9.0"
    old.title = "Earlier SMBv1 wording"
    before = document.model_dump(mode="json")
    assert guidance_status(document)["refresh_available"]
    refreshed = refresh_guidance(document)
    saved = next(finding for finding in refreshed.findings if finding.rule_id == "R08")
    for key in (
        "finding_id",
        "service_id",
        "device_id",
        "severity",
        "confidence",
        "evidence",
        "created_at",
    ):
        assert getattr(saved, key) == getattr(old, key)
    assert saved.rule_version == "1.0.0"
    assert document.model_dump(mode="json") == before
    assert refreshed.guidance_history[0].findings == document.findings


def test_guidance_refresh_never_adds_new_configuration_findings_to_old_report():
    device, services = fixtures()
    document = scan_document(device, services)
    document.findings = [finding for finding in document.findings if finding.rule_id == "R05"]
    refreshed = refresh_guidance(document)
    assert [finding.rule_id for finding in refreshed.findings] == ["R05"]


@pytest.mark.asyncio
async def test_reviewed_smb_ai_choices_keep_limitations_and_hide_identifiers(tmp_path):
    device, services = fixtures()
    document = scan_document(device, services)
    before = deepcopy(document.model_dump(mode="json"))
    payload = build_safe_findings(document)
    encoded = json.dumps(payload)
    for private in (
        device.ip,
        device.mac,
        device.hostname,
        PROTOCOLS,
        OPTIONAL_SIGNING,
        services[0].service_id,
        device.device_id,
    ):
        assert private not in encoded
    for finding in document.findings:
        plain = plain_finding(finding)
        assert plain["title"] == wording_choices(finding.title)[-1]
        for line in finding.limitations:
            choices = wording_choices(line)
            assert len(choices) == 2
            assert validated_line(
                line, choices[-1], field="limitations", rule_id=finding.rule_id
            ) == (choices[-1], True)
    assert document.model_dump(mode="json") == before
    store = JsonStore(tmp_path)
    await store.create_scan(document)
    saved = await ExplanationService(store, ReviewedProvider()).explain_scan(document.scan_id)
    assert all(record.status == "ready" for record in saved.explanations)
    assert saved.findings == document.findings
    assert all(record.prompt_version == PROMPT_VERSION for record in saved.explanations)
    assert all(
        len(rule["meaning"].split()) <= 35 and len(rule["why_it_matters"].split()) <= 35
        for rule in RULE_CATALOGUE.values()
    )
