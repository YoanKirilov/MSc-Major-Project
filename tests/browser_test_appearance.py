"""Appearance preferences and readable themes, using only synthetic reports.

These are focused browser regressions, not an accessibility certification. The
shared fixture rejects real scanners/providers and checks saved evidence bytes.
"""

import os
import re
from pathlib import Path
from uuid import uuid4

import pytest
from app.storage.json_store import JsonStore
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as _report_ui
from tests.fixtures.browser import (
    assert_page_reflows,
    component_boxes,
    scroll_history_with_keyboard,
)

ui = _report_ui

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in browsers"),
]


def _preferences(page):
    dialog = page.locator("#supportingInfoDialog")
    if not dialog.evaluate("element => element.open"):
        page.locator('[data-supporting-topic="accessibility"]').click()
    return dialog.locator(".reading-options")


def _navigate(page, url):
    page.goto(url)
    # WebKit reports cancelled same-origin fetches as access-control page errors
    # when synthetic tests navigate again before initial report/status GETs end.
    # Settle those real initial reads instead of filtering or hiding exceptions.
    page.wait_for_load_state("networkidle")


def _assert_preferences(page, theme, text_size, reduced):
    from playwright.sync_api import expect

    root = page.locator("html")
    expect(root).to_have_attribute("data-theme", theme)
    expect(root).to_have_attribute("data-text-size", text_size)
    expect(root).to_have_attribute("data-reduce-motion", str(reduced).lower())


def test_appearance_controls_replace_justification_and_persist_across_pages(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    page.emulate_media(reduced_motion="no-preference")
    page, _ = _open(ui)
    _assert_preferences(page, "dark", "standard", False)
    expect(page.locator("#textAlignment")).to_have_count(0)
    assert page.locator("#detailPanel .detail-block p").first.evaluate(
        "element => getComputedStyle(element).textAlign"
    ) in {"left", "start"}
    _preferences(page)
    page.get_by_label("Colour theme", exact=True).select_option("light")
    page.get_by_label("Text size", exact=True).select_option("larger")
    expect(page.get_by_label("Movement on screen", exact=True)).to_have_count(0)
    _assert_preferences(page, "light", "larger", False)
    saved = page.evaluate("JSON.parse(localStorage.getItem('netguard-appearance-v1'))")
    assert saved and "justify" not in str(saved) and "motion" not in saved
    page.reload()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    _preferences(page)
    expect(page.locator("#themePreference")).to_have_value("light")
    expect(page.locator("#textSizePreference")).to_have_value("larger")
    expect(page.locator("#motionPreference")).to_have_count(0)
    for route in ("/", "/settings", "/history", f"/scans/{reports['zero'].scan_id}"):
        _navigate(page, base + route)
        _assert_preferences(page, "light", "larger", False)


def test_device_theme_is_consistent_across_settings_report_and_other_tabs(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    page.emulate_media(color_scheme="light")
    _navigate(page, base + "/settings")
    page.get_by_label("Colour theme", exact=True).select_option("system")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    expect(page.locator("#appearance-feedback")).to_contain_text("remembered")
    _navigate(page, base + f"/scans/{reports['zero'].scan_id}")
    panel = _preferences(page)
    expect(panel.locator("#themePreference")).to_have_value("system")
    page.emulate_media(color_scheme="dark")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(panel.locator("#themePreference")).to_have_value("system")
    expect(panel.locator("#appearance-feedback")).to_have_attribute("role", "status")
    other = page.context.new_page()
    try:
        other.emulate_media(color_scheme="light")
        _navigate(other, base + "/settings")
        expect(other.locator("#themePreference")).to_have_value("system")
        other.get_by_label("Colour theme", exact=True).select_option("light")
        expect(panel.locator("#themePreference")).to_have_value("light")
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        other.get_by_label("Colour theme", exact=True).select_option("system")
        expect(panel.locator("#themePreference")).to_have_value("system")
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        expect(other.locator("html")).to_have_attribute("data-theme", "light")
    finally:
        other.close()


def test_settings_keeps_display_choices_without_duplicate_header_link(ui, tmp_path):
    from playwright.sync_api import expect

    page, base, reports = ui
    page.set_viewport_size({"width": 320, "height": 568})
    page.emulate_media(reduced_motion="no-preference")
    mutations = []
    page.on(
        "request",
        lambda request: (
            mutations.append(request.url)
            if "/api/" in request.url and request.method not in {"GET", "OPTIONS"}
            else None
        ),
    )
    for route in ("/", "/history", f"/scans/{reports['zero'].scan_id}", "/settings"):
        _navigate(page, base + route)
        link = page.get_by_role("link", name="Display preferences", exact=True)
        expect(link).to_have_count(0)
        assert_page_reflows(page, route)
    _navigate(page, base + "/")
    page.locator('nav[aria-label="Main navigation"]').get_by_role(
        "link", name="Settings", exact=True
    ).focus()
    page.keyboard.press("Enter")
    page.wait_for_url(base + "/settings")
    page.wait_for_load_state("networkidle")
    panel = page.locator("#display-preferences")
    expect(panel).to_be_visible()
    page.get_by_label("Colour theme", exact=True).focus()
    expect(page.locator("#settings-form #themePreference")).to_have_count(0)
    expect(page.get_by_label("Colour theme", exact=True)).to_be_focused()
    page.get_by_label("Colour theme", exact=True).select_option("light")
    page.get_by_label("Text size", exact=True).select_option("larger")
    expect(page.get_by_label("Movement on screen", exact=True)).to_have_count(0)
    _assert_preferences(page, "light", "larger", False)
    expect(page.locator("#display-preferences-note")).to_contain_text("without pressing Save")
    for control in panel.locator("select").all():
        rect = control.bounding_box()
        assert rect["height"] >= 44 and rect["width"] <= 320
    assert_page_reflows(page, "Settings display preferences, larger text")
    page.locator("#themePreference").scroll_into_view_if_needed()
    page.screenshot(path=tmp_path / "settings-display-preferences-larger-320.png")
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#themePreference")).to_have_value("light")
    expect(page.locator("#textSizePreference")).to_have_value("larger")
    expect(page.locator("#motionPreference")).to_have_count(0)
    _navigate(page, base + f"/scans/{reports['zero'].scan_id}")
    _preferences(page)
    expect(page.locator("#themePreference")).to_have_value("light")
    expect(page.locator("#textSizePreference")).to_have_value("larger")
    expect(page.locator("#motionPreference")).to_have_count(0)
    assert not mutations, f"Display choices must never save app settings or start work: {mutations}"


def test_display_choices_work_with_blocked_storage_and_unavailable_app_settings(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    page.add_init_script(
        """Object.defineProperty(window, 'localStorage', {get() {
          throw new DOMException('Synthetic browser storage denied', 'SecurityError');
        }});"""
    )
    page.route(
        "**/api/settings",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"detail":"Synthetic saved settings unavailable"}',
        ),
    )
    _navigate(page, base + "/settings#display-preferences")
    expect(page.locator("#settings-errors")).to_be_visible()
    expect(page.locator("#save-settings")).to_be_disabled()
    panel = page.locator("#display-preferences")
    expect(panel).to_be_visible()
    page.get_by_label("Colour theme", exact=True).select_option("light")
    page.get_by_label("Text size", exact=True).select_option("larger")
    _assert_preferences(page, "light", "larger", True)
    expect(panel.locator("#appearance-storage-notice")).to_contain_text(
        "could not remember them for later"
    )
    page.get_by_label("Colour theme", exact=True).select_option("dark")
    expect(panel.locator("#appearance-storage-notice")).to_have_count(1)


def test_settings_controls_fit_fieldsets_with_long_choices_and_enlarged_text(ui, tmp_path):
    from playwright.sync_api import expect

    page, base, _ = ui
    _navigate(page, base + "/settings")
    expect(page.locator("#save-settings")).to_be_enabled()
    page.locator(".settings-advanced > summary").click()
    # Change only the synthetic DOM, not saved settings or a real network adapter.
    page.locator("#interface-select").evaluate(
        """select => select.replaceChildren(new Option(
            'SyntheticNetworkAdapterWithAnUnbrokenIdentifier'.repeat(4), '', true, true))"""
    )
    page.locator("#manual-network-field").evaluate("element => element.hidden = false")
    page.locator("#allowed-network").evaluate("element => element.value = '192.168.56.0/24'")
    for scale in ("100%", "125%", "200%"):
        page.evaluate("scale => document.documentElement.style.fontSize = scale", scale)
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            assert_page_reflows(page, f"Expanded Settings at {width}px, {scale} text")
            bounds = page.locator("#settings-form fieldset").evaluate_all(
                """fieldsets => fieldsets.map(fieldset => {
                    const parent = fieldset.getBoundingClientRect();
                    return {width: parent.width, children: [...fieldset.querySelectorAll(
                        'legend, input:not([type=checkbox]), select, button')].map(child => {
                        const rect = child.getBoundingClientRect();
                        return {tag: child.tagName, id: child.id, left: rect.left - parent.left,
                            right: rect.right - parent.left, width: rect.width,
                            height: rect.height};
                    })};
                })"""
            )
            for fieldset in bounds:
                for child in fieldset["children"]:
                    assert child["left"] >= -1 and child["right"] <= fieldset["width"] + 1, (
                        f"{width}px / {scale}: {fieldset}"
                    )
                    if child["tag"] != "LEGEND":
                        assert child["height"] >= 44, child
    page.set_viewport_size({"width": 320, "height": 900})
    page.locator(".settings-advanced").scroll_into_view_if_needed()
    page.screenshot(path=tmp_path / "expanded-settings-200-percent-320.png")


def test_reflow_diagnostics_restore_styles_and_never_turn_overflow_into_a_pass(ui):
    page, base, _ = ui
    page.set_viewport_size({"width": 320, "height": 900})
    _navigate(page, base + "/settings")
    selectors = (
        ".topbar, #display-preferences, #settings-form, #scope-mode, "
        ".settings-advanced, #check-ai, .site-footer"
    )
    nodes = page.locator(selectors)
    page.locator(".topbar").evaluate(
        "node => node.style.setProperty('padding-top', '17px', 'important')"
    )
    style_state = "nodes => nodes.map(node => [node.style.cssText, getComputedStyle(node).display])"
    original = nodes.evaluate_all(style_state)
    page.evaluate(
        """() => { const node = document.createElement('div');
            node.id = 'synthetic-overflow'; node.textContent = 'Synthetic overflow';
            document.body.append(node);
            node.style.width = '400px'; }"""
    )
    observed = page.locator("#synthetic-overflow").evaluate(
        """node => ({width: node.getBoundingClientRect().width,
            inline: node.getAttribute('style'), viewport: innerWidth,
            root: document.documentElement.scrollWidth, body: document.body.scrollWidth,
            display: getComputedStyle(node).display, cssWidth: getComputedStyle(node).width,
            maxWidth: getComputedStyle(node).maxWidth,
            rootOverflow: getComputedStyle(document.documentElement).overflowX,
            bodyOverflow: getComputedStyle(document.body).overflowX})"""
    )
    assert observed["root"] >= 400, str(observed)
    with pytest.raises(AssertionError, match="synthetic-overflow"):
        assert_page_reflows(page, "Deliberately oversized synthetic node")
    assert nodes.evaluate_all(style_state) == original
    assert page.evaluate("document.documentElement.scrollWidth") >= 400
    page.locator("#synthetic-overflow").evaluate("node => node.remove()")
    assert_page_reflows(page, "Original Settings restored after diagnosis")


def test_system_reduced_motion_is_automatic_and_removed_app_preference_is_ignored(ui):
    from playwright.sync_api import expect

    page, _ = _open(ui)
    _preferences(page)
    expect(page.get_by_label("Movement on screen", exact=True)).to_have_count(0)
    page.emulate_media(reduced_motion="reduce")
    _assert_preferences(page, "dark", "standard", True)
    assert (
        page.locator("html").evaluate("element => getComputedStyle(element).scrollBehavior")
        == "auto"
    )
    page.emulate_media(reduced_motion="no-preference")
    _assert_preferences(page, "dark", "standard", False)
    page.evaluate(
        """localStorage.setItem('netguard-appearance-v1', JSON.stringify({
            version: 1, theme: 'light', textSize: 'larger', motion: 'reduce'
        }))"""
    )
    page.reload()
    expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
    _assert_preferences(page, "light", "larger", False)
    page.emulate_media(reduced_motion="reduce")
    _assert_preferences(page, "light", "larger", True)
    expect(page.locator("#motionPreference")).to_have_count(0)


def test_themes_and_larger_text_reflow_on_narrow_and_wide_pages(ui, tmp_path):
    from playwright.sync_api import expect

    page, base, reports = ui
    page, _ = _open(ui, size=(320, 568))
    standard_size = page.locator("body").evaluate(
        "element => parseFloat(getComputedStyle(element).fontSize)"
    )
    _preferences(page)
    page.locator("#textSizePreference").select_option("larger")
    larger_size = page.locator("body").evaluate(
        "element => parseFloat(getComputedStyle(element).fontSize)"
    )
    assert larger_size > standard_size
    for theme in ("dark", "light"):
        _navigate(page, base + f"/scans/{reports['rich'].scan_id}")
        expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
        _preferences(page)
        page.locator("#themePreference").select_option(theme)
        for width, height in ((320, 568), (1440, 1000)):
            page.set_viewport_size({"width": width, "height": height})
            for route in ("/", "/history", "/settings", f"/scans/{reports['rich'].scan_id}"):
                _navigate(page, base + route)
                if route.startswith("/scans/"):
                    expect(page.locator("#report-content")).to_have_attribute(
                        "data-reading-ready", "true"
                    )
                assert_page_reflows(page, f"{theme} larger text, {route} at {width}px")
                if route == "/history":
                    _, scan_type, completion = component_boxes(
                        page.locator("#history-filters"),
                        ".form-field:has(#history-profile)",
                        ".form-field:has(#history-state)",
                    )
                    if width == 1440:
                        assert abs(scan_type["y"] - completion["y"]) <= 1
                        assert completion["x"] > scan_type["x"] + scan_type["width"]
                    else:
                        assert completion["y"] > scan_type["y"] + scan_type["height"]
            _preferences(page)
            controls = page.locator(".reading-options select")
            for control in controls.all():
                rect = control.bounding_box()
                assert rect["height"] >= 44 and rect["width"] <= width
            if width == 320:
                page.locator("#themePreference").scroll_into_view_if_needed()
                page.screenshot(path=tmp_path / f"{theme}-larger-preferences-320.png")
                page.keyboard.press("Escape")
                expect(page.locator("#supportingInfoDialog")).not_to_be_visible()
                page.locator("#detailPanel").scroll_into_view_if_needed()
                page.screenshot(path=tmp_path / f"{theme}-larger-detail-320.png")
                page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
                page.screenshot(path=tmp_path / f"{theme}-larger-overview-320.png")


# Blend translucent backgrounds through their ancestors. Gradient colour stops
# are sampled too, so hard-coded dark detail gradients cannot escape a light
# theme contrast check merely because backgroundColor reports transparent.
_CONTRAST = r"""selectors => {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 1;
  const context = canvas.getContext('2d', {willReadFrequently: true});
  const rgba = value => {
    context.clearRect(0, 0, 1, 1);
    context.fillStyle = value;
    context.fillRect(0, 0, 1, 1);
    const values = Array.from(context.getImageData(0, 0, 1, 1).data);
    return [values[0], values[1], values[2], values[3] / 255];
  };
  const blend = (front, back) => front.slice(0, 3).map(
    (channel, index) => channel * front[3] + back[index] * (1 - front[3]));
  const luminance = values => values.map(value => value / 255).map(
    value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4
  ).reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
  const ratio = (a, b) => {
    const x = luminance(a), y = luminance(b);
    return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
  };
  const backgrounds = element => {
    const ancestors = [];
    for (let cursor = element; cursor; cursor = cursor.parentElement) ancestors.unshift(cursor);
    let variants = [rgba(getComputedStyle(document.documentElement).getPropertyValue('--bg'))];
    for (const ancestor of ancestors) {
      const style = getComputedStyle(ancestor);
      const solid = rgba(style.backgroundColor);
      variants = variants.map(back => blend(solid, back));
      if (style.backgroundImage !== 'none') {
        const pattern = /rgba?\([^)]*\)|#[\da-f]{3,8}\b|color\([^)]*\)|oklch\([^)]*\)/gi;
        const colours = style.backgroundImage.match(pattern) || [];
        if (colours.length) variants = variants.flatMap(back =>
          colours.map(colour => blend(rgba(colour), back))).slice(0, 16);
      }
    }
    return variants;
  };
  const results = [];
  for (const selector of selectors) {
    for (const element of document.querySelectorAll(selector)) {
      if (!element.getClientRects().length || element.closest('[hidden]')
          || element.matches(':disabled')) continue;
      const style = getComputedStyle(element);
      const backgroundsHere = backgrounds(element);
      const foreground = rgba(style.color);
      results.push({selector, text: element.textContent.trim().slice(0, 70),
        colour: style.color, backgrounds: backgroundsHere,
        ratio: Math.min(...backgroundsHere.map(back => ratio(blend(foreground, back), back)))});
    }
  }
  return results;
}"""


def test_light_and_dark_actual_report_text_and_focus_have_readable_contrast(ui):
    page, _ = _open(ui, size=(1440, 1000))
    selectors = [
        ".hero-lead",
        ".status-label",
        ".filter-chip:not(.active)",
        ".filter-chip.active",
        ".filter-chip.active span",
        ".finding-title",
        ".finding-feature",
        ".severity-badge",
        ".detail-panel h3",
        ".detail-location",
        ".detail-block h4",
        ".detail-block p",
        ".remediation-list li > span",
        ".confidence",
        ".reading-options label",
        ".reading-options p",
        ".site-footer p",
    ]
    _preferences(page)
    for theme in ("dark", "light"):
        page.locator("#themePreference").select_option(theme)
        results = page.evaluate(_CONTRAST, selectors)
        assert results, "Contrast audit must inspect real visible text"
        failures = [result for result in results if result["ratio"] < 4.5 - 0.01]
        assert not failures, f"{theme} text contrast below 4.5:1: {failures}"
        control = page.locator("#themePreference")
        control.focus()
        # Keyboard traversal, rather than mouse focus, activates :focus-visible
        # consistently in Chromium, Firefox and WebKit.
        page.keyboard.press("Tab")
        focused = page.locator(":focus")
        outline = focused.evaluate(
            """element => { const style = getComputedStyle(element); return {
                width: parseFloat(style.outlineWidth), style: style.outlineStyle,
                colour: style.outlineColor, surface: style.backgroundColor}; }"""
        )
        assert outline["width"] >= 2 and outline["style"] != "none", outline
        foreground = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", outline["colour"])][:3]
        surface = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", outline["surface"])][:3]

        def luminance(values):
            channels = [value / 255 for value in values]
            linear = [
                value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                for value in channels
            ]
            return sum(
                value * weight
                for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
            )

        first, second = luminance(foreground), luminance(surface)
        assert (max(first, second) + 0.05) / (min(first, second) + 0.05) >= 3, outline


def test_report_name_colour_keeps_scan_type_and_swaps_on_hover(ui):
    from playwright.sync_api import expect

    page, base, reports = ui
    deep = reports["zero"].model_copy(deep=True)
    deep.scan_id = str(uuid4())
    deep.policy["profile"] = "deep-tcp-v1"
    for device in deep.devices:
        device.scan_id = deep.scan_id
    JsonStore(Path(os.environ["APP_DATA_DIR"]))._create_scan(deep)
    for theme in ("dark", "light"):
        _navigate(page, base + f"/scans/{reports['rich'].scan_id}")
        expect(page.locator("#report-content")).to_have_attribute("data-reading-ready", "true")
        _preferences(page)
        page.locator("#themePreference").select_option(theme)
        colours = {}
        for profile in ("light", "deep-tcp-v1"):
            _navigate(page, base + "/history")
            page.locator("#history-profile").select_option(profile)
            page.get_by_role("button", name="Search reports", exact=True).click()
            scroll_history_with_keyboard(page)
            link = page.locator(f"#history-list a[data-profile='{profile}']").first
            expect(link).to_be_visible()
            page.mouse.move(0, 0)
            normal = link.locator("strong").evaluate("element => getComputedStyle(element).color")
            link.hover()
            hovered = link.locator("strong").evaluate("element => getComputedStyle(element).color")
            assert normal != hovered
            colours[profile] = (normal, hovered)
            # Visited history links must still identify the saved scan's type.
            target = link.get_attribute("href")
            assert target
            _navigate(page, base + target)
            _navigate(page, base + "/history")
            page.locator("#history-profile").select_option(profile)
            page.get_by_role("button", name="Search reports", exact=True).click()
            scroll_history_with_keyboard(page)
            link = page.locator(f"#history-list a[data-profile='{profile}']").first
            expect(link).to_be_visible()
            page.mouse.move(0, 0)
            assert (
                link.locator("strong").evaluate("element => getComputedStyle(element).color")
                == normal
            )
        assert colours["light"][0] == colours["deep-tcp-v1"][1]
        assert colours["deep-tcp-v1"][0] == colours["light"][1]
