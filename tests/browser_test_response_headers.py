"""Actual browser enforcement, startup, report and print under response-header CSP."""

import os

import pytest
from app.security.headers import LOCAL_RESPONSE_HEADERS
from tests.browser_test_ui_ux import _open
from tests.browser_test_ui_ux import ui as ui
from tests.fixtures.browser import wait_for_js

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="Opt-in synthetic browsers"),
]


def test_old_backend_contract_keeps_reports_readable_and_blocks_only_cve_write(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    submissions = []

    def old_contract(route):
        request = route.request
        if request.method == "POST" and request.url.endswith("/cves"):
            submissions.append(request.url)
            route.abort()
            return
        response = route.fetch()
        route.fulfill(
            response=response,
            headers={**response.headers, "x-netguard-contract": "1"},
        )

    page.route("**/api/**", old_contract)
    page.goto(base + "/settings")
    expect(page.locator("#save-settings")).to_be_enabled()
    expect(page.locator("#backend-build-note")).to_have_count(1)
    expect(page.locator("#backend-build-note")).to_contain_text("Saved reports remain readable")
    page.locator(".settings-advanced").evaluate("element => element.open = true")
    expect(page.locator("#build-status")).to_contain_text("API contract 3")
    _open(ui)
    expect(page.locator("#backend-build-note")).to_have_count(1)
    wait_for_js(page, "document.querySelector('#report-content').dataset.readingReady === 'true'")
    result = page.evaluate("""async () => {
        const {request} = await import('/static/js/api.js');
        try {
            await request('/api/live-scans/synthetic/services/synthetic/cves',
                {method:'POST', body:'{}'});
            return {unexpected:true};
        } catch (error) { return {status:error.status, message:error.message}; }
    }""")
    assert result["status"] == 409 and "needs restarting" in result["message"]
    assert not submissions


def test_response_policy_allows_the_app_and_print_but_blocks_inline_scripts(ui):
    from playwright.sync_api import expect

    page, base, _ = ui
    page.add_init_script("""(() => {
        window.policyViolations = [];
        document.addEventListener('securitypolicyviolation', event =>
            window.policyViolations.push(event.effectiveDirective));
    })();""")
    for route, selector in (("/", "#scanLaunchButton"), ("/settings", "#save-settings")):
        response = page.goto(base + route)
        for name, value in LOCAL_RESPONSE_HEADERS.items():
            assert response.headers[name.lower()] == value
        expect(page.locator(selector)).to_be_enabled()
        assert not page.evaluate("window.policyViolations")
    _open(ui)
    expect(page.locator("#finding-metric")).to_have_count(0)
    expect(page.locator("#result-count")).to_have_count(1)
    page.get_by_role("button", name="Print or export", exact=True).click()
    preview = page.locator("#report-export-dialog .report-export-preview")
    expect(preview).to_be_visible()
    expect(preview).to_contain_text("Device")
    page.emulate_media(media="print")
    assert page.locator(".page-shell").evaluate("node => getComputedStyle(node).display") == "none"
    assert preview.evaluate("node => getComputedStyle(node).display") != "none"
    page.emulate_media(media="screen")
    assert not page.evaluate("window.policyViolations")
    page.evaluate("""() => {
        window.inlineScriptRan = false;
        const script = document.createElement('script');
        script.textContent = 'window.inlineScriptRan = true';
        document.head.append(script);
    }""")
    wait_for_js(page, "window.policyViolations.some(value => value.startsWith('script-src'))")
    assert page.evaluate("window.inlineScriptRan") is False
