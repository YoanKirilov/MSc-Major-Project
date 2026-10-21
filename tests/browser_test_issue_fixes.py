"""Real-engine UI acceptance for 21 October edges; all scan replies synthetic."""

import os
from time import monotonic
from uuid import uuid4

import pytest
from app.build_info import API_CONTRACT_VERSION
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui
from tests.fixtures.browser import assert_page_reflows, wait_for_report_ready

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browsers"),
]


def wait_for_routes(page, pending, count):
    """The request event precedes route dispatch in Firefox; wait for that callback."""
    deadline = monotonic() + 10
    while len(pending) < count and monotonic() < deadline:
        page.wait_for_timeout(20)
    assert len(pending) == count


@pytest.mark.parametrize("old_status", [202, 409, 503])
def test_superseded_post_never_replaces_newer_scan(ui, old_status):
    from playwright.sync_api import expect

    page, base, reports = ui
    pending = []
    page.route("**/api/live-scans", lambda route: pending.append(route))
    page.goto(base + "/light")
    expect(page.locator("#scanLaunchButton")).to_be_enabled()
    with page.expect_request("**/api/live-scans"):
        page.locator("#scanLaunchButton").click()
    wait_for_routes(page, pending, 1)
    first_operation = page.url.split("#start=")[1]
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#scanStartReset").click()
    with page.expect_request("**/api/live-scans"):
        page.locator("#scanLaunchButton").click()
    wait_for_routes(page, pending, 2)
    newer_operation = page.url.split("#start=")[1]
    assert first_operation != newer_operation and len(pending) == 2
    headers = {"X-NetGuard-Contract": str(API_CONTRACT_VERSION)}
    with page.expect_response("**/api/live-scans"):
        pending[0].fulfill(
            status=old_status,
            headers=headers,
            json={"scan_id": reports["rich"].scan_id}
            if old_status == 202
            else {"detail": "Earlier attempt outcome"},
        )
    # Drain browser tasks/paint, not a fixed network sleep; the old handler must settle.
    page.evaluate(
        "async () => { await new Promise(requestAnimationFrame); "
        "await new Promise(requestAnimationFrame); }"
    )
    assert page.url.endswith("#start=" + newer_operation)
    expect(page.locator("#scanLaunchButton")).to_be_disabled()
    expect(page.locator("#scanError")).to_be_hidden()
    pending[1].fulfill(status=202, headers=headers, json={"scan_id": reports["zero"].scan_id})
    page.wait_for_url(base + f"/scans/{reports['zero'].scan_id}")
    wait_for_report_ready(page)
    assert len(pending) == 2


@pytest.mark.parametrize("receipt_status", [401, 503])
def test_pending_recovery_does_not_need_status_and_keeps_retry_visible(ui, receipt_status):
    from playwright.sync_api import expect

    page, base, reports = ui
    operation = str(uuid4())
    status_reads = []
    writes = []
    page.on(
        "request", lambda request: writes.append(request.url) if request.method == "POST" else None
    )
    page.route(
        "**/api/status",
        lambda route: (
            status_reads.append(route.request.url),
            route.fulfill(status=503, json={"detail": "Synthetic status outage"}),
        ),
    )
    path = f"**/api/scan-starts/{operation}"
    page.route(
        path,
        lambda route: route.fulfill(
            status=receipt_status, json={"detail": "Synthetic receipt outage"}
        ),
    )
    page.goto(base + f"/light#start={operation}")
    expect(page.locator("#scanStartRecover")).to_be_visible()
    expect(page.locator("#scanStartRecover")).to_be_enabled()
    expect(page.locator("#scanLaunchButton")).to_be_disabled()
    if receipt_status == 401:
        expect(page.locator("#scanError")).to_contain_text("session has expired")
    assert not status_reads and not writes
    page.unroute(path)
    page.route(
        path,
        lambda route: route.fulfill(json={"state": "accepted", "scan_id": reports["zero"].scan_id}),
    )
    page.locator("#scanStartRecover").click()
    page.wait_for_url(base + f"/scans/{reports['zero'].scan_id}")
    wait_for_report_ready(page)
    assert not status_reads and not writes


def test_interrupted_discovery_has_honest_summary_metric_and_technical_empty_state(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    report = reports["empty"]

    def interrupted(route):
        response = route.fetch()
        data = response.json()
        data.update(state="failed", scan_outcome="failed")
        data["coverage"]["discovery_complete"] = False
        route.fulfill(response=response, json=data)

    page.route(f"**/api/live-scans/{report.scan_id}", interrupted)
    _open(ui, kind="empty", size=(390, 844))
    expect(page.locator("#result-title")).to_contain_text("Could not complete")
    expect(page.locator("#result-coverage")).to_contain_text("device search did not finish")
    expect(page.locator("#device-metric")).to_have_text("Search incomplete")
    expect(page.locator("#device-table-body")).to_contain_text("device search did not finish")
    assert "No devices answered the search" not in page.locator("body").inner_text()
    for width in (320, 390, 768, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        assert_page_reflows(page, f"interrupted discovery at {width}px")
