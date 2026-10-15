import httpx
import pytest
from app.scanner.cpe import product_cpe, service_product_cpe
from app.scanner.cve import LOOKUP_VERSION, NVD_API, NvdClient
from tests.unit.test_cves import QUERY, nvd_data, software

PRODUCT = "cpe:2.3:a:apache:http_server:*:*:*:*:*:*:*:*"


def related_data():
    exact = nvd_data()["vulnerabilities"][0]
    rows = [exact]
    for index in range(10):
        rows.append(
            {
                "cve": {
                    "id": f"CVE-2026-{10000 + index}",
                    "vulnStatus": "Analyzed",
                    "descriptions": [{"lang": "en", "value": "Synthetic related issue."}],
                    "configurations": [
                        {
                            "nodes": [
                                {
                                    "cpeMatch": [
                                        {
                                            "vulnerable": True,
                                            "criteria": QUERY.replace("2.4.49", "2.4.40"),
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                }
            }
        )
    return {"totalResults": len(rows), "vulnerabilities": rows}


@pytest.mark.asyncio
async def test_exact_and_related_queries_are_separate_deduplicated_and_bounded():
    calls = []

    def handler(request):
        calls.append(request)
        assert str(request.url).startswith(NVD_API)
        if "cpeName" in request.url.params:
            return httpx.Response(200, json=nvd_data())
        assert dict(request.url.params) == {
            "virtualMatchString": PRODUCT,
            "noRejected": "",
            "resultsPerPage": "20",
        }
        data = related_data()
        data["vulnerabilities"][0]["cve"]["configurations"] = [
            {"nodes": [{"cpeMatch": [{"vulnerable": True, "criteria": QUERY}]}]}
        ]
        return httpx.Response(200, json=data)

    client = NvdClient(httpx.MockTransport(handler))
    client.request_interval_s = 0
    result = await client.lookup(software())
    assert result.lookup_version == LOOKUP_VERSION
    assert result.status == "candidates" and result.total == 1
    assert result.related_status == "candidates" and result.related_query == PRODUCT
    assert len(result.related_results) == 5 and result.related_truncated
    assert len(calls) == 2
    assert {r.cve_id for r in result.results}.isdisjoint(r.cve_id for r in result.related_results)


@pytest.mark.asyncio
async def test_related_lookup_works_for_a_known_product_without_inventing_a_version():
    calls = []

    def handler(request):
        calls.append(request)
        assert "cpeName" not in request.url.params
        return httpx.Response(200, json=related_data())

    result = await NvdClient(httpx.MockTransport(handler)).lookup(
        software(cpes=["cpe:/a:apache:http_server"])
    )
    assert result.status == "insufficient_evidence" and result.query is None
    assert not result.results
    assert result.related_status == "candidates" and len(calls) == 1
    assert "version was not identified" in result.message


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", ["other_product", "not_vulnerable", "negated", "rejected"])
async def test_unrelated_negative_and_rejected_records_are_not_presented_as_related(mutation):
    data = related_data()
    row = data["vulnerabilities"][1]["cve"]
    node = row["configurations"][0]["nodes"][0]
    if mutation == "other_product":
        node["cpeMatch"][0]["criteria"] = QUERY.replace("http_server", "unrelated_product")
    elif mutation == "not_vulnerable":
        node["cpeMatch"][0]["vulnerable"] = False
    elif mutation == "negated":
        row["configurations"][0]["negate"] = True
    else:
        row["vulnStatus"] = "Rejected"
    data = {"totalResults": 1, "vulnerabilities": [{"cve": row}]}
    result = await NvdClient(httpx.MockTransport(lambda _: httpx.Response(200, json=data))).lookup(
        software(cpes=["cpe:/a:apache:http_server"])
    )
    assert result.related_status == "no_matches" and not result.related_results


@pytest.mark.asyncio
async def test_failed_related_search_preserves_the_version_references():
    def handler(request):
        if "cpeName" in request.url.params:
            return httpx.Response(200, json=nvd_data())
        return httpx.Response(429)

    client = NvdClient(httpx.MockTransport(handler))
    client.request_interval_s = 0
    result = await client.lookup(software())
    assert result.status == "candidates" and len(result.results) == 1
    assert result.related_status == "unavailable"


@pytest.mark.asyncio
async def test_insufficient_or_ambiguous_products_do_not_send_any_query():
    def forbidden(_):
        pytest.fail("No product means no NVD request")

    client = NvdClient(httpx.MockTransport(forbidden))
    for changes in [
        {"cpes": []},
        {"cpes": ["cpe:/o:linux:linux_kernel:5.0"]},
        {"nmap_confidence": 6},
        {"detection_method": "table"},
        {"cpes": [QUERY, QUERY.replace("apache", "other_vendor")]},
    ]:
        result = await client.lookup(software(**changes))
        assert result.status == "insufficient_evidence"
        assert result.related_status == "not_requested"


def test_product_identity_does_not_guess_aliases_or_broaden_ports():
    assert product_cpe("cpe:/a:apache:http_server") == PRODUCT
    assert product_cpe(QUERY) == PRODUCT
    for value in [
        None,
        "cpe:/o:apache:http_server:2.4.49",
        "cpe:/a:*:http_server:2.4.49",
        "cpe:/a:apache:http_server:2%3a4",
        "cpe:/a:apache:http_server:latest",
    ]:
        assert product_cpe(value) is None
    assert service_product_cpe(software(cpes=[])) is None
