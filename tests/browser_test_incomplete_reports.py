"""Compact failed reports retain explicit coverage, technical evidence and retry."""

import os

import pytest
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui
from tests.fixtures.browser import assert_page_reflows

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browsers"),
]


def test_failed_report_is_compact_without_disguising_unchecked_devices(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    report = reports["failed"]

    def interrupted(route):
        response = route.fetch()
        data = response.json()
        data.update(state="failed", scan_outcome="failed")
        data["coverage"]["targets"][0].update(
            service_status="cancelled", reason_code="network_interrupted"
        )
        data["errors"] = [
            {
                "code": "NETWORK_INTERRUPTED",
                "reason": "list_timeout",
                "message": "Local interface verification took too long. Scanning stopped.",
            }
        ]
        route.fulfill(response=response, json=data)

    page.route(f"**/api/live-scans/{report.scan_id}", interrupted)
    _open(ui, kind="failed", size=(390, 844))
    expect(page.locator("#result-lead")).to_contain_text("stopped before usable device results")
    expect(page.locator("#result-lead")).not_to_contain_text("0 features")
    expect(page.locator("#retryHostsButton")).to_be_visible()
    expect(page.locator("#searchInput")).to_be_hidden()
    expect(page.locator("#reviewDevice")).to_be_hidden()
    expect(page.locator(".findings-section .filter-row")).to_be_hidden()
    expect(page.locator("#detailPanel")).to_be_hidden()
    expect(page.locator(".next-steps")).to_be_hidden()
    expect(page.locator("#deviceSearchInput")).to_be_hidden()
    expect(page.locator("#resultsSummary")).to_contain_text("Scan incomplete")
    expect(page.locator("#device-summaries")).to_contain_text("connection could not be verified")
    expect(page.locator("#device-search-count")).to_contain_text("0 checked; 1 unfinished")
    notes = page.locator("#scan-problems details")
    expect(notes).not_to_have_attribute("open", "")
    notes.locator("summary").press("Enter")
    expect(notes).to_contain_text("192.168.56.231")
    expect(page.locator("#technical-devices")).to_be_visible()
    for width in (320, 390, 768, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        assert_page_reflows(page, f"compact incomplete report {width}")


def test_completed_empty_report_hides_unused_controls_but_keeps_coverage(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui, kind="zero", size=(320, 568))
    expect(page.locator("#result-title")).to_contain_text("ready")
    expect(page.locator("#resultsSummary")).to_contain_text("does not prove")
    expect(page.locator("#searchInput")).to_be_hidden()
    expect(page.locator("#device-summaries .device-summary-group")).to_have_count(1)
    expect(page.locator("#technical-devices")).to_be_visible()
    expect(page.locator("#result-coverage")).not_to_be_empty()
