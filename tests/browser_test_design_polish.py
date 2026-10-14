"""Polished scan/report feedback using mocked reads, never starting a scan."""

import os

import pytest
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as _report_ui

ui = _report_ui
pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic UI"),
]


def test_mocked_progress_has_honest_status_values_and_spaced_actions(ui, tmp_path):
    from playwright.sync_api import expect

    page, base, _ = ui
    scan_id = "11111111-1111-4111-8111-111111111111"
    phase = {"value": "queued"}
    page.route(
        f"**/api/scans/{scan_id}",
        lambda route: route.fulfill(
            json={"policy": {"profile": "deep-tcp-v1"}, "target": {"hosts": ["192.168.56.10"]}}
        ),
    )

    def saved_progress(route):
        route.fulfill(
            json={
                "state": "running",
                "phase": phase["value"],
                "policy": {"profile": "deep-tcp-v1"},
                "coverage": {"candidate_count": 1},
                "analysis_progress": {"state": "preparing", "total": 4, "completed": 2},
            }
        )

    page.route(f"**/api/live-scans/{scan_id}/progress", saved_progress)
    page.goto(base + f"/#scan={scan_id}")
    # The fixture already opened '/': a fragment-only goto does not reload modules.
    page.reload()
    progress = page.get_by_role("progressbar", name="Overall scan progress")
    expect(page.locator("#progressPercent")).to_have_text("Waiting")
    expect(progress).not_to_have_attribute("aria-valuenow", "0")
    assert progress.get_attribute("aria-valuenow") is None
    expect(page.locator("#scan-config")).to_contain_text("waiting to start")
    for current in ("discovery", "service_scan", "analysis"):
        phase["value"] = current
        expect(page.locator("#progressPhase")).to_have_text(
            {
                "discovery": "Looking for devices",
                "service_scan": "Checking device connections",
                "analysis": "Making your results easier to understand.",
            }[current]
        )
        expect(page.locator("#scan-config")).not_to_contain_text("Ready to scan")
        expect(progress).to_have_attribute("aria-valuemin", "0")
        expect(progress).to_have_attribute("aria-valuemax", "100")
        if current == "analysis":
            expect(progress).to_have_attribute("aria-valuenow", "95")
            expect(page.locator("#scan-config")).to_contain_text("results are saved")
        else:
            assert progress.get_attribute("aria-valuenow") is None
        expect(progress).to_have_attribute("aria-describedby", "progressDetail progressScaleNote")
        expect(page.locator("#progressScaleNote")).to_contain_text("not time remaining")
    for theme in ("dark", "light"):
        page.evaluate("theme => NetGuardAppearance.applyAppearancePreferences({theme})", theme)
        for width, height in ((320, 568), (1440, 1000)):
            page.set_viewport_size({"width": width, "height": height})
            actions = page.locator(".scan-progress-actions")
            controls = (page.locator("#scanCancelButton"), page.locator("#anotherScanLink"))
            boxes = [control.bounding_box() for control in controls]
            for box in boxes:
                assert box["height"] >= 44
                assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1
            first, second = boxes
            assert (
                second["x"] - first["x"] - first["width"] >= 11
                or second["y"] - first["y"] - first["height"] >= 11
            )
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
            geometry = page.evaluate("""() => ({
                setupBottom: document.querySelector('.scan-landing').getBoundingClientRect().bottom,
                progressTop: document.querySelector('#scanProgress').getBoundingClientRect().top
            })""")
            assert geometry["progressTop"] >= geometry["setupBottom"]
            expect(actions).to_have_attribute("aria-label", "Actions for this scan")
            page.screenshot(path=tmp_path / f"progress-{theme}-{width}.png", full_page=True)


def test_missing_deep_address_error_points_to_input_without_submitting(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    page.goto(base + "/deep")
    expect(page.locator("#scanLaunchButton")).to_be_enabled()
    page.locator("#scanLaunchButton").click()
    address = page.locator("#deepHostInput")
    expect(address).to_be_focused()
    expect(address).to_have_attribute("aria-invalid", "true")
    expect(address).to_have_attribute("aria-describedby", "recentDeviceDetails deepHostError")
    expect(page.locator("#deepHostError")).to_contain_text("Enter the address of one device")
    address.fill("192.168.56.10")
    assert address.get_attribute("aria-invalid") is None
    expect(page.locator("#deepHostError")).to_be_hidden()


def test_report_review_and_recovery_actions_have_separate_hierarchy(ui, tmp_path):
    from playwright.sync_api import expect

    page, _ = _open(ui, "rich", (390, 844))
    expect(page.locator("#openFirstFinding")).to_be_visible()
    assert "primary-button" in page.locator("#openFirstFinding").get_attribute("class")
    assert "secondary-button" in page.locator("#runAgainButton").get_attribute("class")
    expect(page.get_by_role("group", name="Report tools")).to_be_visible()
    for width in (320, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        recovery = page.get_by_role("group", name="Recover the report or unfinished checks")
        expect(recovery).to_be_visible()
        expect(recovery.locator("#simplifyButton")).to_be_visible()
        expect(page.locator("#ai-report-notice")).to_contain_text("built-in explanations")
        expect(page.locator("#ai-report-notice")).not_to_contain_text("rule-based")
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
        page.screenshot(path=tmp_path / f"report-actions-{width}.png", full_page=True)
        page.locator("#scan-summary").screenshot(
            path=tmp_path / f"report-action-header-{width}.png"
        )
    page, _ = _open(ui, "failed")
    recovery = page.get_by_role("group", name="Recover the report or unfinished checks")
    expect(recovery.locator("#retryHostsButton")).to_be_visible()
    expect(recovery.locator("#simplifyButton")).to_be_visible()


def test_recovery_actions_remain_visible_without_has_layout_support(ui):
    from playwright.sync_api import expect

    page, _, _ = ui

    def older_layout_rules(route):
        response = route.fetch()
        # Model lack of :has support without changing browser versions/security.
        css = "\n".join(line for line in response.text().splitlines() if ":has(" not in line)
        route.fulfill(response=response, body=css)

    page.route("**/static/css/app.css", older_layout_rules)
    page, _ = _open(ui, "failed")
    recovery = page.get_by_role("group", name="Recover the report or unfinished checks")
    expect(recovery.locator("#retryHostsButton")).to_be_visible()
    expect(recovery.locator("#simplifyButton")).to_be_visible()
