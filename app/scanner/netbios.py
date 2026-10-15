"""Extract a single endpoint-bound computer name, never user or raw NetBIOS data."""

import re

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

MAX_NAME_XML_BYTES = 65536
MAX_NAME_OUTPUT = 2048


def computer_name(stdout, address):
    """A missing or ambiguous reply is unavailable, not a guessed device identity."""
    if not stdout or len(stdout) > MAX_NAME_XML_BYTES:
        return None, "The computer-name reply was missing or exceeded its size limit."
    try:
        root = ElementTree.fromstring(stdout)
    except (ValueError, ElementTree.ParseError, DefusedXmlException):
        return None, "The computer-name reply could not be read reliably."
    hosts = root.findall("host")
    if root.tag != "nmaprun" or len(hosts) != 1:
        return None, "The reply did not identify one unambiguous device."
    statuses = hosts[0].findall("status")
    if (
        hosts[0].get("timedout") == "true"
        or len(statuses) > 1
        or (statuses and statuses[0].get("state") != "up")
    ):
        return None, "The computer-name check did not record a completed device reply."
    addresses = [
        node.get("addr")
        for node in hosts[0].findall("address")
        if node.get("addrtype") in {None, "ipv4"}
    ]
    scripts = hosts[0].findall("hostscript/script[@id='nbstat']")
    if addresses != [address] or len(scripts) != 1:
        return None, "The reply did not identify one unambiguous device and name check."
    output = scripts[0].get("output", "")
    if (
        not output
        or len(output) > MAX_NAME_OUTPUT
        or re.search(
            r"^\s*(?:ERROR|Script execution failed)\b", output, re.MULTILINE | re.IGNORECASE
        )
    ):
        return None, "No complete usable computer-name reply was returned."
    # Match the documented summary, not usernames or the verbose names/group table.
    matches = re.findall(r"(?:^|\n)[ \t]*NetBIOS name:[ \t]*([^,\r\n]+),", output)
    if len(matches) != 1 or output.count("NetBIOS name:") != 1:
        return None, "The reply did not contain one unambiguous computer name."
    name = matches[0].strip()
    if not name or len(name) > 255 or name.casefold() in {"<unknown>", "unknown", "*", "(none)"}:
        return None, "No computer name was returned."
    if any(not char.isprintable() for char in name):
        return None, "The computer name contained unsupported characters."
    return name, None
