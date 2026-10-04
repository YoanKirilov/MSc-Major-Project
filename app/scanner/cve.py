"""Bounded NVD references for explicit, versioned application CPEs; never port guesses."""

import asyncio
import json
import re
from time import monotonic

import httpx

from app.schemas.common import iso_z, utc_now
from app.schemas.cve import CveLookup, CveReference

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MAX_RESPONSE_BYTES = 1_000_000


def application_cpe(value: str) -> str | None:
    """Accept the simple lossless subset; never broaden escaped/packed CPE names."""
    if value.startswith("cpe:/"):
        fields = value[5:].split(":")
        if not 4 <= len(fields) <= 7:
            return None
        fields = [part or "*" for part in fields] + ["*"] * (11 - len(fields))
    elif value.startswith("cpe:2.3:"):
        fields = value[8:].split(":")
        if len(fields) != 11:
            return None
    else:
        return None
    if fields[0] != "a" or any(part in {"*", "-"} for part in fields[1:4]):
        return None
    if not any(char.isdigit() for char in fields[3]):
        return None
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}|\*", part) for part in fields):
        return None
    return "cpe:2.3:" + ":".join(fields)


def service_cpe(service) -> str | None:
    if service.state != "open" or service.detection_method != "probed":
        return None
    if service.nmap_confidence is None or service.nmap_confidence < 7:
        return None
    identities = {cpe for raw in service.cpes if (cpe := application_cpe(raw))}
    return next(iter(identities)) if len(identities) == 1 else None


class NvdBusy(Exception):
    pass


class NvdClient:
    def __init__(self, transport=None):
        self.transport = transport
        self.lock = asyncio.Lock()
        self.next_request = 0.0
        self.request_interval_s = 6.5

    async def _fetch_json(self, url, params):
        await asyncio.sleep(max(0, self.next_request - monotonic()))
        self.next_request = monotonic() + self.request_interval_s
        async with asyncio.timeout(8):
            async with httpx.AsyncClient(
                timeout=7, transport=self.transport, trust_env=False, follow_redirects=False
            ) as client:
                async with client.stream("GET", url, params=params) as response:
                    if response.status_code in {403, 429}:
                        self.next_request = monotonic() + 30
                    response.raise_for_status()
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise ValueError("oversized NVD response")
        return json.loads(body)

    async def lookup(self, service) -> CveLookup:
        query = service_cpe(service)
        common = {"service_id": service.service_id, "checked_at": iso_z(utc_now()), "query": query}
        if query is None:
            return CveLookup(
                **common,
                status="insufficient_evidence",
                message=(
                    "A port alone cannot identify a CVE. This result needs one confidently "
                    "detected software fingerprint with a specific version. A new Deep scan "
                    "may collect it, but some devices do not reveal their software."
                ),
            )
        if self.lock.locked() or monotonic() < self.next_request:
            raise NvdBusy
        async with self.lock:
            try:
                async with asyncio.timeout(45):
                    params = {
                        "cpeName": query,
                        "isVulnerable": "",
                        "noRejected": "",
                        "resultsPerPage": 5,
                    }
                    data = await self._fetch_json(NVD_API, params)
                    if (
                        type(data.get("totalResults")) is int
                        and data["totalResults"] == 0
                        and data.get("vulnerabilities") == []
                    ):
                        from app.scanner.cpe_identity import resolve_identity

                        resolved, method, evidence = await resolve_identity(query, self._fetch_json)
                        common.update(
                            resolved_query=resolved, resolution=method, identity_evidence=evidence
                        )
                        if not resolved:
                            return CveLookup(
                                **common,
                                status="identity_unresolved",
                                message=(
                                    "The software fingerprint could not be matched unambiguously "
                                    "to the product dictionary. This is not a verified no-matches "
                                    "result; check the device maker's advice."
                                ),
                            )
                        if resolved != query:
                            data = await self._fetch_json(NVD_API, {**params, "cpeName": resolved})
                total = data["totalResults"]
                entries = data["vulnerabilities"]
                if type(total) is not int or total < 0 or not isinstance(entries, list):
                    raise ValueError("invalid NVD response")
                if len(entries) > 5 or total < len(entries) or (total and not entries):
                    raise ValueError("inconsistent NVD response")
                results = []
                seen = set()
                for entry in entries:
                    cve = entry["cve"]
                    if cve.get("vulnStatus") == "Rejected":
                        continue
                    description = next(
                        (d["value"] for d in cve["descriptions"] if d.get("lang") == "en"),
                        "Open the published record for its description.",
                    )
                    record = CveReference(
                        cve_id=cve["id"], description=" ".join(description.split())[:1200]
                    )
                    if record.cve_id not in seen:
                        results.append(record)
                        seen.add(record.cve_id)
                if total and not results:
                    raise ValueError("no usable records")
                return CveLookup(
                    **common,
                    status="candidates" if results else "no_matches",
                    total=total,
                    results=results,
                    truncated=total > len(results),
                    message=(
                        "NVD returned possible software/version matches. This does not confirm "
                        "that this device is affected; configuration and vendor fixes still matter."
                        if results
                        else "NVD returned no matches for this software fingerprint. This does not "
                        "prove the device is safe; records or product mappings may be incomplete."
                    ),
                )
            except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError, AttributeError):
                return CveLookup(
                    **common,
                    status="unavailable",
                    message=(
                        "The CVE database could not be checked. Try again later; "
                        "this is not a no-matches result."
                    ),
                )
