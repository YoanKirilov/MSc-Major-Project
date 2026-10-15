import asyncio
import html

import pytest
from app.scanner.details import netbios_name
from app.scanner.netbios import computer_name
from app.scanner.runner import ProcessResult
from app.schemas.scan import Device, Service

IP = "192.168.56.10"
SUMMARY = "NetBIOS name: LAPTOP, NetBIOS user: PRIVATE-USER, NetBIOS MAC: aa:bb:cc:dd:ee:02"


def reply(output=SUMMARY, ip=IP, extra_script="", extra_host=""):
    return (
        f'<nmaprun><host><address addr="{ip}" addrtype="ipv4"/>'
        f'<address addr="aa:bb:cc:dd:ee:02" addrtype="mac"/><hostscript>'
        f'<script id="nbstat" output="{html.escape(output, quote=True)}"/>'
        f"{extra_script}</hostscript></host>{extra_host}</nmaprun>"
    ).encode()


def test_extracts_only_one_computer_name_never_users_groups_or_raw_output():
    assert computer_name(reply(), IP) == ("LAPTOP", None)
    assert "PRIVATE-USER" not in str(computer_name(reply(), IP))
    verbose = SUMMARY + "\n Names:\n   PRIVATE-GROUP<00> Flags: group active"
    assert computer_name(reply(verbose), IP) == ("LAPTOP", None)


@pytest.mark.parametrize(
    "xml",
    [
        b"",
        b"invalid",
        b"x" * 65537,
        reply(ip="192.168.56.11"),
        reply(extra_host=f'<host><address addr="{IP}"/></host>'),
        reply(extra_script='<script id="nbstat" output="NetBIOS name: OTHER,"/>'),
        reply(SUMMARY + "\nNetBIOS name: OTHER, NetBIOS user: PRIVATE"),
        reply(SUMMARY + "\nNetBIOS name: LAPTOP, NetBIOS user: PRIVATE"),
        reply("ERROR: failed\n" + SUMMARY),
        reply("Script execution failed\n" + SUMMARY),
        reply("NetBIOS name: <unknown>, NetBIOS user: PRIVATE"),
        reply("NetBIOS name: LAPTOP"),
        reply("NetBIOS name: " + "x" * 256 + ","),
        reply("x" * 2049),
        b'<!DOCTYPE nmaprun [<!ENTITY x "private">]><nmaprun>&x;</nmaprun>',
    ],
    ids=lambda value: f"reply-{len(value)}-bytes",
)
def test_missing_ambiguous_invalid_or_unbounded_replies_never_select_a_name(xml):
    name, reason = computer_name(xml, IP)
    assert name is None and reason
    assert "PRIVATE" not in reason


def test_duplicate_or_wrong_family_addresses_are_not_endpoint_evidence():
    for xml in [
        reply().replace(b'addrtype="ipv4"', b'addrtype="ipv6"'),
        reply().replace(b"<hostscript>", f'<address addr="{IP}"/><hostscript>'.encode()),
    ]:
        assert computer_name(xml, IP)[0] is None


@pytest.mark.parametrize(
    "host",
    [
        b'<host timedout="true">',
        b'<host><status state="down"/>',
        b'<host><status state="up"/><status state="up"/>',
    ],
)
def test_explicit_unfinished_or_conflicting_host_status_is_unavailable(host):
    assert computer_name(reply().replace(b"<host>", host), IP)[0] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fault,expected",
    [
        ({"timed_out": True}, "ran out of time"),
        ({"cancelled": True}, "cancelled"),
        ({"overflow": True}, "size limit"),
        ({"returncode": 2}, "scanner error"),
        ({"returncode": None}, "scanner error"),
    ],
)
async def test_process_failure_never_adopts_a_partial_name_or_username(fault, expected):
    async def runner(*args):
        return ProcessResult(
            **{
                "stdout": reply(),
                "stderr": b"PRIVATE-USER",
                "returncode": 0,
                "duration_s": 0.1,
                **fault,
            }
        )

    device = Device(device_id="device", scan_id="synthetic", ip=IP)
    service = Service(service_id="service", device_id="device", port=445, state="open")
    await netbios_name(device, [service], "nmap", runner, asyncio.Event())
    assert device.hostname is None and not device.name_candidates
    assert device.details[0].status == "unavailable"
    assert expected in device.details[0].value
    assert "PRIVATE-USER" not in device.model_dump_json()
