"""Bounded NVD references for explicit, versioned application CPEs; never port guesses."""

import asyncio
import json
from time import monotonic

import httpx

from app.schemas.advisory import CveAdvisory
from app.schemas.common import iso_z, utc_now
from app.schemas.cve import CveLookup, CveReference

from .cpe import application_cpe as application_cpe
from .cpe import product_cpe, service_product_cpe
from .cpe import service_cpe as service_cpe

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MAX_RESPONSE_BYTES = 1_000_000
LOOKUP_VERSION = "product-research-3"


def _entries(data, limit):
    total, rows = data["totalResults"], data["vulnerabilities"]
    if type(total) is not int or total < 0 or not isinstance(rows, list):
        raise ValueError("invalid NVD response")
    if len(rows) > limit or total < len(rows) or (total and not rows):
        raise ValueError("inconsistent NVD response")
    return total, rows


def _reference(cve):
    description = next(
        (d["value"] for d in cve["descriptions"] if d.get("lang") == "en"),
        "Open the published record for its description.",
    )
    advisories = []
    seen = set()
    references = cve.get("references", [])
    for reference in references[:40] if isinstance(references, list) else []:
        if (
            not isinstance(reference, dict)
            or not isinstance(reference.get("tags"), list)
            or "Vendor Advisory" not in reference["tags"]
        ):
            continue
        try:
            advisory = CveAdvisory(url=reference.get("url"))
        except (ValueError, TypeError):
            continue
        if advisory.url not in seen:
            seen.add(advisory.url)
            advisories.append(advisory)
        if len(advisories) == 3:
            break
    return CveReference(
        cve_id=cve["id"], description=" ".join(description.split())[:1200], advisories=advisories
    )


def product_applicability(cve, product):
    # A description/port coincidence is not enough. Inspect only positive,
    # non-negated vulnerable product criteria; keep bounds on nested input.
    configurations = cve.get("configurations")
    if not isinstance(configurations, list) or not configurations:
        return "unknown"
    pending = list(configurations)
    visited = 0
    unknown = False
    while pending and visited < 200:
        node = pending.pop()
        visited += 1
        if not isinstance(node, dict):
            unknown = True
            continue
        if node.get("negate") is True:
            continue
        if "negate" in node and type(node["negate"]) is not bool:
            unknown = True
            continue
        matches = node.get("cpeMatch", [])
        children = []
        for key in ("nodes", "children"):
            value = node.get(key, [])
            if not isinstance(value, list):
                unknown = True
            else:
                children.extend(value[:201])
                unknown |= len(value) > 200
        if not isinstance(matches, list):
            unknown = True
            matches = []
        if not matches and not children:
            unknown = True
        for match in matches[:200]:
            if not isinstance(match, dict) or type(match.get("vulnerable")) is not bool:
                unknown = True
                continue
            if not match["vulnerable"]:
                continue
            identity = product_cpe(match.get("criteria"))
            if identity is None:
                unknown = True
            elif identity == product:
                return "related"
        unknown |= len(matches) > 200
        pending.extend(children)
    return "unknown" if pending or unknown else "not_related"


def _related_to_product(cve, product):
    """Compatibility boolean for callers that require positive evidence only."""
    return product_applicability(cve, product) == "related"


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
        product = service_product_cpe(service)
        common = {
            "service_id": service.service_id,
            "checked_at": iso_z(utc_now()),
            "query": query,
            "lookup_version": LOOKUP_VERSION,
        }
        if product is None:
            return CveLookup(
                **common,
                status="insufficient_evidence",
                message=(
                    "A port alone cannot identify a CVE. This result needs one confidently "
                    "detected software product. A new Deep scan "
                    "may collect it, but some devices do not reveal their software."
                ),
            )
        if self.lock.locked() or monotonic() < self.next_request:
            raise NvdBusy
        async with self.lock:
            result = None
            try:
                async with asyncio.timeout(45):
                    result = await self._version_lookup(query, common)
                    product = product_cpe(result.resolved_query) or product
                    result.related_query = product
                    data = await self._fetch_json(
                        NVD_API,
                        {"virtualMatchString": product, "noRejected": "", "resultsPerPage": 20},
                    )
                    total, entries = _entries(data, 20)
                    seen = {record.cve_id for record in result.results}
                    related = []
                    unverified = 0
                    for entry in entries:
                        cve = entry["cve"]
                        if cve.get("vulnStatus") in {"Rejected", "REJECT"}:
                            continue
                        applicability = product_applicability(cve, product)
                        if applicability == "unknown":
                            unverified += 1
                            continue
                        if applicability != "related":
                            continue
                        record = _reference(cve)
                        if record.cve_id not in seen:
                            seen.add(record.cve_id)
                            related.append(record)
                    result.related_total = total
                    result.related_results = related[:5]
                    result.related_truncated = total > len(entries) or len(related) > 5
                    result.related_unverified = unverified
                    result.related_status = (
                        "candidates"
                        if related
                        else "coverage_unknown"
                        if unverified
                        else "no_matches"
                    )
                    return result
            except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError, AttributeError):
                if result is not None:
                    result.related_status = "unavailable"
                    return result
                return CveLookup(
                    **common,
                    status="unavailable",
                    message=(
                        "The CVE database could not be checked. Try again later; "
                        "this is not a no-matches result."
                    ),
                )

    async def _version_lookup(self, query, common):
        if query is None:
            return CveLookup(
                **common,
                status="insufficient_evidence",
                message="The software product was recorded, but its version was not identified "
                "unambiguously. Related product references below are research leads only.",
            )
        params = {"cpeName": query, "isVulnerable": "", "noRejected": "", "resultsPerPage": 5}
        data = await self._fetch_json(NVD_API, params)
        total, entries = _entries(data, 5)
        if total == 0:
            from app.scanner.cpe_identity import resolve_identity

            resolved, method, evidence = await resolve_identity(query, self._fetch_json)
            common.update(resolved_query=resolved, resolution=method, identity_evidence=evidence)
            if not resolved:
                return CveLookup(
                    **common,
                    status="identity_unresolved",
                    message="The versioned fingerprint could not be matched reliably to the "
                    "product dictionary. Related records are not confirmation of this identity.",
                )
            if resolved != query:
                data = await self._fetch_json(NVD_API, {**params, "cpeName": resolved})
                total, entries = _entries(data, 5)
        results = []
        seen = set()
        for entry in entries:
            cve = entry["cve"]
            if cve.get("vulnStatus") in {"Rejected", "REJECT"}:
                continue
            record = _reference(cve)
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
