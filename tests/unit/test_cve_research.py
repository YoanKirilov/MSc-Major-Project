"""Bounded related research must be useful without asserting device applicability."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
from app.main import create_app
from app.scanner.cve import NvdClient
from app.schemas.common import iso_z, utc_now
from app.schemas.cve import CveReference
from app.schemas.scan import ScanDocument
from app.security.session import SessionManager
from app.storage.annotations import AnnotationStore
from fastapi.testclient import TestClient
from tests.session_helpers import BASE_URL, authenticate_client
from tests.unit.test_cve_related import PRODUCT
from tests.unit.test_cves import QUERY, software


def page(total, offset=0, *, related=True):
    rows = []
    for index in range(offset, min(offset + 20, total)):
        published = datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(days=index)
        rows.append(
            {
                "cve": {
                    "id": f"CVE-2020-{20000 + index}",
                    "published": published.isoformat().replace("+00:00", ""),
                    "lastModified": "2026-10-20T12:00:00.000",
                    "descriptions": [{"lang": "en", "value": "Synthetic product case."}],
                    "configurations": [
                        {
                            "nodes": [
                                {
                                    "cpeMatch": [
                                        {
                                            "vulnerable": True,
                                            "criteria": QUERY
                                            if related
                                            else QUERY.replace("apache", "unrelated"),
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                }
            }
        )
    return {"startIndex": offset, "totalResults": total, "vulnerabilities": rows}


async def lookup(handler):
    client = NvdClient(httpx.MockTransport(handler))
    client.request_interval_s = 0
    return await client.lookup(software(cpes=["cpe:/a:apache:http_server"]))


@pytest.mark.asyncio
async def test_recent_related_versions_are_found_without_an_exact_version():
    calls = []

    def handler(request):
        calls.append(dict(request.url.params))
        assert request.url.params["virtualMatchString"] == PRODUCT
        return httpx.Response(200, json=page(35, int(request.url.params.get("startIndex", 0))))

    result = await lookup(handler)
    assert result.query is None and result.status == "insufficient_evidence"
    assert not result.results
    assert result.related_status == "candidates"
    assert [r.cve_id for r in result.related_results] == [
        f"CVE-2020-{20000 + i}" for i in range(34, 29, -1)
    ]
    assert result.related_examined == 35
    assert result.related_total == 35 and result.related_truncated
    assert result.related_selection == "recent_first" and not result.related_search_incomplete
    assert len(calls) == 2 and calls[1]["startIndex"] == "15"
    assert result.related_results[0].published_at == "2020-02-04T00:00:00Z"
    assert result.related_results[0].modified_at == "2026-10-20T12:00:00Z"


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", ["http", "offset", "changed_total", "short_page"])
async def test_failed_or_unstable_recent_page_preserves_first_page_leads(fault):
    def handler(request):
        offset = int(request.url.params.get("startIndex", 0))
        data = page(35, offset)
        if offset:
            if fault == "http":
                return httpx.Response(429)
            if fault == "offset":
                data["startIndex"] = 0
            elif fault == "changed_total":
                data["totalResults"] = 36
            else:
                data["vulnerabilities"].pop()
        return httpx.Response(200, json=data)

    result = await lookup(handler)
    assert result.related_status == "candidates" and len(result.related_results) == 5
    assert result.related_examined == 20 and result.related_search_incomplete
    assert result.related_truncated and result.related_selection == "partial"
    assert result.related_results[0].cve_id == "CVE-2020-20019"


@pytest.mark.asyncio
async def test_large_history_uses_only_two_pages_and_never_port_or_device_queries():
    calls = []

    def handler(request):
        calls.append(dict(request.url.params))
        assert set(request.url.params) <= {
            "virtualMatchString",
            "noRejected",
            "resultsPerPage",
            "startIndex",
        }
        return httpx.Response(200, json=page(200, int(request.url.params.get("startIndex", 0))))

    result = await lookup(handler)
    assert len(calls) == 2 and calls[-1]["startIndex"] == "180"
    assert result.related_examined == 40 and result.related_truncated
    assert len(result.related_results) == 5


@pytest.mark.asyncio
async def test_unexamined_history_cannot_be_a_no_related_problems_result():
    result = await lookup(
        lambda request: httpx.Response(
            200, json=page(200, int(request.url.params.get("startIndex", 0)), related=False)
        )
    )
    assert result.related_status == "coverage_unknown"
    assert result.related_truncated and not result.related_results


@pytest.mark.parametrize(
    "date", [None, "bad", "2026-02-30T00:00:00Z", "2026-01-01", "2026-01-01T12:00:00"]
)
def test_old_or_invalid_saved_dates_are_not_invented(date):
    record = CveReference(cve_id="CVE-2026-12345", description="Example", published_at=date)
    assert record.published_at is None


def test_partial_product_search_is_not_reused_as_a_complete_day_long_cache():

    from app.scanner.cve import LOOKUP_VERSION
    from app.schemas.cve import CveLookup

    manager = SessionManager()
    app = create_app(session_manager=manager)
    service = software(cpes=["cpe:/a:apache:http_server"])
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"totalResults": 0, "vulnerabilities": []})

    with TestClient(app, base_url=BASE_URL) as client:
        doc = ScanDocument(
            scan_id=str(uuid4()),
            phase="finished",
            state="completed",
            target={"mode": "known_hosts", "hosts": ["192.168.0.10"]},
            services=[service],
        )
        app.state.store._create_scan(doc)
        AnnotationStore(app.state.store)._update(
            doc.scan_id,
            cve=CveLookup(
                service_id=service.service_id,
                checked_at=iso_z(utc_now()),
                query=None,
                related_query=PRODUCT,
                status="insufficient_evidence",
                message="Partial search",
                lookup_version=LOOKUP_VERSION,
                related_status="candidates",
                related_search_incomplete=True,
            ),
        )
        original = (app.state.store._scan_dir(doc.scan_id) / "scan.json").read_bytes()
        app.state.nvd = NvdClient(httpx.MockTransport(handler))
        app.state.explanations.provider = None
        response = client.post(
            f"/api/live-scans/{doc.scan_id}/services/{service.service_id}/cves",
            json={},
            headers=authenticate_client(client, manager),
        )
        assert response.status_code == 200
        assert len(calls) == 1 and not response.json().get("cached", False)
        assert not response.json()["lookup"]["related_search_incomplete"]
        assert (app.state.store._scan_dir(doc.scan_id) / "scan.json").read_bytes() == original
