"""Interpret saved certificate date evidence; never request or validate a certificate."""

import re
from datetime import datetime, timezone

from app.schemas.common import iso_z, observation_time

DATE_LINE = re.compile(r"^[ \t]*Not valid (before|after):[ \t]*(\S+)[ \t]*$", re.MULTILINE)
NMAP_DATE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?")
LIMITATION = (
    "Dates alone do not verify who runs this connection, whether a browser trusts it, "
    "or the device's safety. Do not bypass browser warnings."
)


def certificate_dates(service):
    """Return (plain text, status) only for ssl-cert evidence at this saved endpoint."""
    scripts = [entry for entry in service.script_results if entry.script_id == "ssl-cert"]
    if not scripts:
        return None
    unavailable = (
        "The certificate's date window could not be checked reliably from the saved reply. "
        "A complete start date, end date and recorded check time are needed. " + LIMITATION,
        "unavailable",
    )
    if len(scripts) != 1 or service.state != "open":
        return unavailable
    script = scripts[0]
    if (
        script.truncated
        or len(script.output) > 1024
        or re.search(
            r"^\s*(?:ERROR|Script execution failed)\b", script.output, re.MULTILINE | re.IGNORECASE
        )
    ):
        return unavailable
    output = script.output.replace("\r\n", "\n")
    lines = DATE_LINE.findall(output)
    markers = re.findall(r"^[ \t]*Not valid (?:before|after):", output, re.MULTILINE)
    if len(markers) != 2 or len(lines) != 2 or {kind for kind, _ in lines} != {"before", "after"}:
        return unavailable
    if any(NMAP_DATE.fullmatch(value) is None for _, value in lines):
        return unavailable
    try:
        dates = {
            kind: datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
            for kind, value in lines
        }
    except (ValueError, TypeError):
        return unavailable
    checked = observation_time(service.observed_at)
    if checked is None or dates["before"] > dates["after"]:
        return unavailable
    if checked < dates["before"]:
        summary = "The certificate was not yet within its date window when checked."
    elif checked > dates["after"]:
        summary = "The certificate had expired when checked."
    else:
        summary = (
            "The certificate was within its date window when checked; this is not a safety pass."
        )
    return (
        f"{summary} Recorded check: {iso_z(checked)}. "
        f"Date window: {iso_z(dates['before'])} to {iso_z(dates['after'])}. {LIMITATION}",
        "observed",
    )
