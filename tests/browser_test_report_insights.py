"""Device-first report tasks against synthetic isolated facts; no scan traffic."""

import os

import pytest
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui
from tests.fixtures.browser import wait_for_js

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browsers"),
]


@pytest.mark.parametrize("width", [320, 390, 1440])
def test_report_simple_search_and_feature_view_keep_all_saved_facts(ui, width):
    from playwright.sync_api import expect

    page, report = _open(ui, size=(width, 844))
    expect(page.locator("#changes-overview")).to_contain_text("not available")
    expect(page.locator("#shareReportButton")).to_be_enabled()
    total = page.locator(".device-summary-group").count()
    expect(page.locator("#deviceQuickFilter")).to_have_count(0)
    page.get_by_role("searchbox", name="Search devices", exact=True).fill("192.168.56.231")
    expect(page.locator(".device-summary-group")).to_have_count(1)
    expect(page.locator(".device-summary-group")).to_contain_text("could not finish")
    page.get_by_role("button", name="Clear", exact=True).click()
    expect(page.locator(".device-summary-group")).to_have_count(total)
    page.locator("#feature-inventory > summary").click()
    expect(page.locator("#feature-inventory-list")).to_contain_text("File sharing")
    page.locator("#feature-inventory-list").get_by_role(
        "button", name="View this device"
    ).first.click()
    expect(page.locator(".device-summary-group")).to_have_count(1)
    expect(page.locator(".device-summary")).to_have_attribute("open", "")
    page.get_by_label("Show review tasks", exact=True).select_option("need_help")
    expect(page.locator("#checklist-filter")).to_have_value("need_help")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert len(report.services) == 13


def test_export_preview_is_redacted_and_print_does_not_include_underlying_report(ui):
    from playwright.sync_api import expect

    page, _report = _open(ui)
    page.get_by_role("button", name="Print or export", exact=True).click()
    dialog = page.locator("#report-export-dialog")
    expect(dialog).to_be_visible()
    wait_for_js(
        page,
        "document.querySelector('#report-export-dialog .report-export-preview')"
        "?.textContent.length > 80",
    )
    assert "192.168.56." not in dialog.inner_text()
    assert "VeryLongReportedDeviceName" not in dialog.inner_text()
    page.emulate_media(media="print")
    assert page.locator(".page-shell").evaluate("node => getComputedStyle(node).display") == "none"
    assert dialog.evaluate("node => getComputedStyle(node).display") != "none"
    page.emulate_media(media="screen")
