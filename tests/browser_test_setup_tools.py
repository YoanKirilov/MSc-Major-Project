"""Device choices and parallel-job controls with synthetic, read-only browser data."""

import os

import pytest
from tests.browser_test_ui_ux import ui as _report_ui

ui = _report_ui

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browsers"),
]


def test_native_picker_keeps_choices_short_and_saved_context_separate(ui, tmp_path):
    from playwright.sync_api import expect

    page, base, _ = ui
    address = "192.168.0.10"
    items = [
        {
            "ip": address,
            "name": "Kitchen TV",
            "observed_at": "2026-10-12T18:00:00Z",
            "last_check": "Address saved; response not confirmed",
        },
        {
            "ip": "192.168.0.11",
            "name": "Unnamed device",
            "observed_at": None,
            "last_check": "Last device check did not finish",
        },
    ]
    writes = []
    page.on(
        "request",
        lambda request: (
            writes.append(request.url)
            if "/api/" in request.url and request.method not in {"GET", "OPTIONS"}
            else None
        ),
    )
    page.route(
        "**/api/recent-devices",
        lambda route: route.fulfill(json={"items": items, "days": 7, "warnings": []}),
    )
    page.goto(base + "/deep")
    page.wait_for_load_state("networkidle")
    select = page.locator("#recentDeviceSelect")
    expect(select.locator("option")).to_have_count(3)
    expect(select.locator("option").nth(1)).to_have_text("Kitchen TV — 192.168.0.10")
    expect(select).not_to_contain_text("response not confirmed")
    expect(select).to_have_attribute("aria-describedby", "recentDeviceNote recentDeviceDetails")
    assert select.evaluate("element => element.tagName") == "SELECT"
    select.select_option(address)
    expect(page.locator("#deepHostInput")).to_have_value(address)
    expect(page.locator("#recentDeviceDetails")).to_contain_text("response not confirmed")
    expect(page.locator("#recentDeviceDetails")).to_contain_text(
        "not a check of whether the device is connected now"
    )
    select.focus()
    page.keyboard.press("Tab")
    expect(page.locator("#refreshDeviceChoices")).to_be_focused()
    for width, font_scale in ((320, 100), (1280, 100), (320, 200)):
        page.set_viewport_size({"width": width, "height": 900})
        page.evaluate(
            "value => document.documentElement.style.setProperty('font-size', value, 'important')",
            f"{font_scale}%",
        )
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
        for control in (select, page.locator("#deepHostInput")):
            box = control.bounding_box()
            assert box["height"] >= 44
            assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1
        page.screenshot(path=tmp_path / f"picker-context-{width}-{font_scale}.png")
    page.locator("#deepHostInput").fill("192.168.0.99")
    expect(select).to_have_value("")
    expect(page.locator("#recentDeviceDetails")).to_contain_text("entered address")
    expect(page.locator("#recentDeviceDetails")).not_to_contain_text("response not confirmed")
    items.clear()
    page.locator("#refreshDeviceChoices").click()
    expect(select.locator("option")).to_have_count(1)
    expect(page.locator("#deepHostInput")).to_have_value("192.168.0.99")
    expect(page.locator("#recentDeviceNote")).to_contain_text("It has been kept")
    assert not writes, f"Choosing or refreshing a device must not start or mutate a scan: {writes}"


def test_running_job_actions_wrap_with_separate_touch_targets(ui, tmp_path):
    from playwright.sync_api import expect

    page, base, _ = ui
    job_id = "11111111-1111-4111-8111-111111111111"
    page.route(
        "**/api/running-scans",
        lambda route: route.fulfill(
            json={
                "items": [
                    {
                        "scan_id": job_id,
                        "profile": "light",
                        "target": {"hosts": ["192.168.0.10"]},
                        "phase": "service_scan",
                        "completed": 0,
                        "total": 1,
                        "started_at": "2026-10-12T18:00:00Z",
                    }
                ]
            }
        ),
    )
    page.set_viewport_size({"width": 320, "height": 900})
    page.goto(base + "/")
    page.wait_for_load_state("networkidle")
    actions = page.locator("#runningScans .running-scan-actions")
    expect(actions).to_be_visible()
    progress = actions.get_by_role("link", name="Open Light progress", exact=True)
    report = actions.get_by_role("link", name="Open saved report", exact=True)
    cancel = actions.get_by_role("button", name="Cancel Light scan", exact=True)
    expect(progress).to_have_attribute("href", f"/#scan={job_id}")
    expect(report).to_have_attribute("href", f"/scans/{job_id}")
    expect(progress).to_have_attribute("rel", "noopener")
    for width in (320, 1280):
        page.set_viewport_size({"width": width, "height": 900})
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
        boxes = [control.bounding_box() for control in (progress, report, cancel)]
        for box in boxes:
            assert box["height"] >= 44
            assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1
        for first, second in zip(boxes, boxes[1:], strict=False):
            horizontal_gap = second["x"] - first["x"] - first["width"]
            vertical_gap = second["y"] - first["y"] - first["height"]
            assert horizontal_gap >= 8 or vertical_gap >= 8
        page.screenshot(path=tmp_path / f"running-actions-{width}.png", full_page=True)
