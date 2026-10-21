import hashlib
import os
from pathlib import Path
from uuid import uuid4

import pytest
from tests.fixtures.diagnostics import MAX_JOB_BYTES, capture, redact, safe_trace
from tests.fixtures.offline import install_offline_guard


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    secrets = getattr(item, "diagnostic_secrets", set())
    if secrets:
        if isinstance(report.longrepr, tuple):
            report.longrepr = tuple(
                redact(value, secrets) if isinstance(value, str) else value
                for value in report.longrepr
            )
        elif report.longrepr:
            report.longrepr = redact(str(report.longrepr), secrets)
        report.sections = [(name, redact(value, secrets)) for name, value in report.sections]
    if report.when == "teardown" and getattr(item, "publish_diagnostics", None):
        try:
            item.publish_diagnostics()
        except Exception:
            report.sections.append(
                ("diagnostics", "Diagnostic export failed; the test outcome is unchanged.")
            )


@pytest.fixture(autouse=True)
def synthetic_diagnostics(request, monkeypatch, tmp_path):
    export = os.getenv("NETGUARD_DIAGNOSTICS_DIR")
    if (
        not export
        or request.node.get_closest_marker("live_lab")
        or request.node.get_closest_marker("live_provider")
    ):
        yield
        return
    from app.security.session import SessionManager

    secrets = request.node.diagnostic_secrets = set()
    for name in ("__init__", "build_session_cookie", "csrf_for_session"):
        original = getattr(SessionManager, name)

        def wrapped(self, *args, _name=name, _original=original, **kwargs):
            result = _original(self, *args, **kwargs)
            if _name == "__init__":
                secrets.update((self.bootstrap_token, self.csrf_secret))
            elif isinstance(result, str):
                secrets.add(result)
            return result

        monkeypatch.setattr(SessionManager, name, wrapped)
    if not request.node.get_closest_marker("browser"):
        yield
        return
    from playwright.sync_api import Browser, BrowserContext

    raw = tmp_path / "diagnostic-private"
    raw.mkdir()
    contexts = {}
    captured = set()

    def register(context):
        if context not in contexts:
            contexts[context] = len(contexts)
            context.tracing.start(snapshots=True, screenshots=False, sources=False)
        return context

    def finish(context):
        if context in contexts and context not in captured:
            captured.add(context)
            capture(context, raw, contexts[context], secrets)

    new_context, new_page = Browser.new_context, Browser.new_page
    close_context, close_browser = BrowserContext.close, Browser.close

    def context_factory(self, *args, **kwargs):
        return register(new_context(self, *args, **kwargs))

    def page_factory(self, *args, **kwargs):
        page = new_page(self, *args, **kwargs)
        register(page.context)
        return page

    def context_close(self, *args, **kwargs):
        finish(self)
        return close_context(self, *args, **kwargs)

    def browser_close(self, *args, **kwargs):
        for context in self.contexts:
            finish(context)
        return close_browser(self, *args, **kwargs)

    monkeypatch.setattr(Browser, "new_context", context_factory)
    monkeypatch.setattr(Browser, "new_page", page_factory)
    monkeypatch.setattr(BrowserContext, "close", context_close)
    monkeypatch.setattr(Browser, "close", browser_close)
    yield

    def publish():
        failed = any(
            getattr(request.node, f"rep_{phase}", None)
            and getattr(request.node, f"rep_{phase}").failed
            for phase in ("setup", "call", "teardown")
        )
        output = Path(export).resolve()
        workspace = Path(__file__).resolve().parents[1]
        if not output.is_relative_to(workspace / ".test-artifacts") or output.is_symlink():
            raise ValueError("Diagnostics must stay in the owned test-artifact folder")
        output.mkdir(parents=True, exist_ok=True)
        used = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
        key = hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:12] + "-" + uuid4().hex[:6]
        for path in raw.iterdir():
            if failed and path.stat().st_size + used <= MAX_JOB_BYTES:
                target = output / f"{key}-{path.name}"
                try:
                    if path.suffix == ".zip":
                        safe_trace(path, target, secrets)
                    elif path.suffix == ".png":
                        target.write_bytes(path.read_bytes())
                    if target.exists():
                        size = target.stat().st_size
                        if used + size > MAX_JOB_BYTES:
                            target.unlink()
                        else:
                            used += size
                except (OSError, ValueError):
                    if target.is_file():
                        target.unlink()
            # Only this test's own private files, never a recursive directory delete.
            if path.is_file() and path.resolve().is_relative_to(raw.resolve()):
                path.unlink()

    request.node.publish_diagnostics = publish


@pytest.fixture(params=os.getenv("RESPONSIVE_BROWSERS", "chromium").split(","))
def browser_engine(request):
    """Select the actual engine, not a job label around hardcoded Chromium."""
    if request.param not in {"chromium", "firefox", "webkit"}:
        pytest.fail("Unknown browser engine")
    return request.param


@pytest.fixture(autouse=True)
def prevent_live_work_in_synthetic_tests(request, monkeypatch):
    if not request.node.get_closest_marker("live_lab"):
        install_offline_guard(
            monkeypatch, allow_browser=bool(request.node.get_closest_marker("browser"))
        )


@pytest.fixture(autouse=True)
def isolate_application_data(tmp_path, monkeypatch):
    """Tests must never reconcile or write the developer's saved scans."""
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path / "app-data"))
    monkeypatch.setenv("APP_AI_AUTOSTART", "0")
    # Tests opt in to synthetic credentials, never inherit a real Pi-hole secret.
    for name in ("APP_PIHOLE_URL", "APP_PIHOLE_PASSWORD", "APP_PIHOLE_PASSWORD_FILE"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def no_dns_in_offline_tests(request, monkeypatch):
    if request.node.get_closest_marker("live_lab"):
        return

    async def no_hostname(self, ip):
        return None

    monkeypatch.setattr("app.jobs.supervisor.ScanSupervisor._local_hostname", no_hostname)
    # API tests use synthetic scopes, never the developer's current Wi-Fi.
    monkeypatch.setattr("app.api.scans.detect_private_network", lambda: None)
    monkeypatch.setattr("app.api.session.detect_private_network", lambda: None)
    monkeypatch.setattr("app.api.library.detect_private_network", lambda: None)
    monkeypatch.setattr("app.scanner.network.connection_snapshot", lambda *a, **k: {"test": True})

    async def no_extra_network(*args, **kwargs):
        return None

    # Collector unit tests explicitly inject synthetic transports/runners.
    # API/browser tests must not contact synthetic fixture device addresses.
    monkeypatch.setattr("app.scanner.details.network_details", no_extra_network)
    monkeypatch.setattr("app.scanner.details.netbios_name", no_extra_network)
