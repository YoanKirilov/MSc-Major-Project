"""Opt-in Light/home and Deep/this-PC verification; never modify the normal store."""

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.build_info import API_CONTRACT_VERSION, source_build_id  # noqa: E402
from app.config import detect_private_network, load_config  # noqa: E402
from app.scanner.network import connection_snapshot  # noqa: E402
from app.schemas.scan import ScanDocument  # noqa: E402
from app.schemas.settings import Settings  # noqa: E402


def save(run, name, value):
    (run / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def hashes(root):
    result = {}
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                with path.open("rb") as handle:
                    result[str(path.relative_to(root))] = hashlib.file_digest(
                        handle, "sha256"
                    ).hexdigest()
    return result


def read_api(context, path):
    """Only GET is retried; a progress reconnect must never submit another scan."""
    return context.request.get(path, timeout=60000, max_retries=2)


def require_review_success(browser_results, integrity, *, saved_only=False):
    """Recorded diagnostics must affect the outcome, not just an artifact file."""
    if browser_results["page_errors"]:
        raise RuntimeError("Browser errors were recorded; inspect browser-results.json")
    expected = 0 if saved_only else 2
    if browser_results["scan_submissions"] != expected:
        raise RuntimeError(f"Unexpected scan submission count; expected {expected}")
    if not saved_only and browser_results["refresh_kept_both_jobs"] is not True:
        raise RuntimeError("Refreshing did not preserve both running scans")
    if not saved_only and browser_results["automatic_reports_after_analysis"] is not True:
        raise RuntimeError("Automatic navigation after analysis was not verified")
    if integrity["normal_existing_reports_unchanged"] is not True:
        raise RuntimeError("Existing normal reports changed; inspect integrity.json")
    if saved_only and integrity["saved_test_evidence_unchanged"] is not True:
        raise RuntimeError("Saved test evidence changed; inspect integrity.json")


def saved_pair(run):
    """Only reopen isolated, finished reports; startup must not recover live jobs."""
    data = run / "data"
    scan_root = data / "scans"
    if not data.is_dir() or not data.resolve().is_relative_to(run):
        raise ValueError("Saved test data must remain inside the review artifact folder")
    if not scan_root.is_dir() or not scan_root.resolve().is_relative_to(data.resolve()):
        raise ValueError("Saved scans must remain inside the isolated data folder")
    documents = {}
    for path in scan_root.glob("*/scan.json"):
        if not path.resolve().is_relative_to(scan_root.resolve()):
            raise ValueError("Saved scan evidence must not link outside the isolated folder")
        document = ScanDocument.model_validate_json(path.read_bytes())
        if document.phase != "finished" or document.state in {"queued", "running"}:
            raise ValueError("Finish or cancel all test jobs before reopening saved reports")
        documents[document.scan_id] = document
    ids = {}
    for profile, policy in (("light", "light"), ("deep", "deep-tcp-v1")):
        scan_id = str(UUID(json.loads((run / f"{profile}-id.json").read_text())["scan_id"]))
        document = documents.get(scan_id)
        if (
            document is None
            or document.source != "live"
            or document.policy.get("profile") != policy
        ):
            raise ValueError("Saved report identity or profile does not match the review pair")
        ids[profile] = scan_id
    return data, ids


def normal_public_check(run):
    """Inspect served code, not another instance's private session or reports."""
    try:
        if not (ROOT / "app").is_dir():
            raise OSError("Missing source")
        expected_build = source_build_id(ROOT / "app")
    except OSError:
        expected_build = None
    result = {
        "reachable": False,
        "expected_build": expected_build,
        "source_match": None,
        "freshness": "unverified",
        "restart_required": None,
    }
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/openapi.json", timeout=5) as response:
            schema = json.load(response)
        result.update(
            reachable=True,
            deletion_route="/api/reports/delete" in schema["paths"],
            restore_route="/api/reports/restore" in schema["paths"],
            recovery_route="/api/reports/recovery" in schema["paths"],
            capabilities_route="/api/report-capabilities" in schema["paths"],
            device_inventory_route="/api/devices" in schema["paths"],
            device_views_contract=any(
                parameter.get("name") == "view"
                for parameter in schema["paths"]
                .get("/api/devices", {})
                .get("get", {})
                .get("parameters", [])
            ),
            share_route="/api/live-scans/{scan_id}/share" in schema["paths"],
            monitoring_route="/api/monitoring" in schema["paths"],
            cve_operation_contract="operation_id"
            in schema.get("components", {})
            .get("schemas", {})
            .get("CveLookupRequest", {})
            .get("properties", {}),
        )
        mismatches = []
        for path in (ROOT / "app/static").rglob("*"):
            if path.is_file() and path.suffix in {".js", ".mjs", ".css"}:
                route = "/static/" + path.relative_to(ROOT / "app/static").as_posix()
                with urllib.request.urlopen("http://127.0.0.1:8765" + route, timeout=5) as reply:
                    if reply.read() != path.read_bytes():
                        mismatches.append(route)
        result["asset_mismatches"] = mismatches
        with urllib.request.urlopen("http://127.0.0.1:8765/", timeout=5) as reply:
            result["running_contract"] = reply.headers.get("X-NetGuard-Contract")
            result["running_build"] = reply.headers.get("X-NetGuard-Build")
        running = result["running_build"]
        result["source_match"] = (running == expected_build) if running and expected_build else None
        result["freshness"] = {True: "current", False: "different"}.get(
            result["source_match"], "unverified"
        )
        contract_matches = result["cve_operation_contract"] and result["running_contract"] == str(
            API_CONTRACT_VERSION
        )
        result["restart_required"] = (
            True
            if not contract_matches
            else (not result["source_match"] if result["source_match"] is not None else None)
        )
    except Exception as error:
        result["error_type"] = type(error).__name__
    save(run, "normal-public-check.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorised", action="store_true")
    parser.add_argument(
        "--verify-saved", action="store_true", help="Reopen finished test reports only"
    )
    parser.add_argument("--scope")
    parser.add_argument("--host")
    parser.add_argument("--artifacts", required=True, type=Path)
    args = parser.parse_args()
    if not args.verify_saved and not (args.authorised and args.scope and args.host):
        parser.error("Live scans require --authorised, --scope and --host")
    source_run = args.artifacts.resolve()
    if not source_run.is_relative_to(ROOT / ".test-artifacts"):
        parser.error("Use a private folder under .test-artifacts")
    if not args.verify_saved and source_run.exists():
        parser.error("Use a new private folder under .test-artifacts; never reuse scan IDs")
    saved_ids = {}
    if args.verify_saved:
        try:
            data, saved_ids = saved_pair(source_run)
        except (OSError, ValueError, KeyError, TypeError) as error:
            parser.error(f"Cannot reopen saved test reports: {error}")
    run = source_run / f"verification-{uuid4().hex[:10]}" if args.verify_saved else source_run
    try:
        from playwright.sync_api import expect, sync_playwright
    except ModuleNotFoundError:
        parser.error(
            "Playwright is required. Run this helper with the existing .venv-quality "
            "Python environment; the app's .venv runtime does not include browser tools."
        )
    config = load_config()
    if not args.verify_saved:
        if detect_private_network() != args.scope:
            parser.error("The default-route network no longer matches the authorised scope")
        snapshot = connection_snapshot(config, args.scope, strict=True)
        if snapshot["address"] != args.host:
            parser.error("The Deep target must be this PC's confirmed local interface address")
    run.mkdir(parents=True)
    print(f"Live check artifacts: {run}", flush=True)
    normal_root = config.data_dir
    before = hashes(normal_root / "scans")
    save(run, "normal-report-hashes-before.json", before)
    public = normal_public_check(run)
    print(json.dumps({"normal_public_check": public}), flush=True)
    if not args.verify_saved:
        data = run / "data"
        data.mkdir()
        settings_path = normal_root / "settings.json"
        saved = (
            Settings.model_validate_json(settings_path.read_bytes())
            if settings_path.exists()
            else Settings()
        )
        save(run, "normal-settings-facts.json", saved.model_dump())
        # Keep configured name discovery, but never call optional Pi-hole.
        isolated = saved.model_copy(
            update={
                "allowed_network": None,
                "interface": None,
                "retain_raw_xml": True,
                "pihole_enabled": False,
            }
        )
        save(data, "settings.json", isolated.model_dump(mode="json"))
    saved_before = hashes(data / "scans") if args.verify_saved else None
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = {
        **os.environ,
        "APP_DATA_DIR": str(data),
        "APP_PORT": str(port),
        "APP_ALLOWED_NETWORK": "",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for name in ("APP_PIHOLE_URL", "APP_PIHOLE_PASSWORD", "APP_PIHOLE_PASSWORD_FILE"):
        env[name] = ""
    process = browser = context = cancel_headers = None
    scans, errors, submissions = {}, [], []
    try:
        with (
            (run / "backend.stdout.log").open("x") as stdout,
            (run / "backend.stderr.log").open("x") as stderr,
        ):
            process = subprocess.Popen(
                [
                    str(ROOT / ".venv/Scripts/python.exe"),
                    "-B",
                    "-m",
                    "app",
                    "serve",
                    "--port",
                    str(port),
                    "--no-browser",
                ],
                cwd=ROOT,
                env=env,
                stdout=stdout,
                stderr=stderr,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        bootstrap = None
        for _ in range(60):
            if process.poll() is not None:
                raise RuntimeError("Owned test backend exited; inspect its private log")
            matches = re.findall(
                re.escape(base) + r"/#token=[A-Za-z0-9_-]+",
                (run / "backend.stdout.log").read_text(),
            )
            if matches:
                bootstrap = matches[-1]
                break
            time.sleep(1)
        if not bootstrap:
            raise TimeoutError("Owned backend startup deadline")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 390, "height": 844}, reduced_motion="reduce"
            )
            context.on(
                "page", lambda page: page.on("pageerror", lambda error: errors.append(str(error)))
            )
            context.on(
                "request",
                lambda request: (
                    submissions.append(request.url)
                    if request.method == "POST" and request.url.endswith("/api/live-scans")
                    else None
                ),
            )
            welcome = context.new_page()
            with welcome.expect_response(
                lambda response: (
                    response.request.method == "POST" and response.url.endswith("/api/session")
                )
            ) as authentication:
                welcome.goto(bootstrap, wait_until="domcontentloaded")
            if authentication.value.status != 200:
                raise RuntimeError("The owned test session could not be opened")
            if not args.verify_saved:
                expect(welcome.locator("#scanLaunchButton")).to_be_enabled(timeout=60000)
            preflight = read_api(context, base + "/api/status").json()
            session = read_api(context, base + "/api/session").json()
            cookie = next(
                item["value"] for item in context.cookies() if item["name"] == "session_id"
            )
            cancel_headers = {
                "Origin": base,
                "Content-Type": "application/json",
                "Cookie": f"session_id={cookie}",
                "X-CSRF-Token": session["csrf_token"],
            }
            save(run, "preflight.json", preflight)
            if not args.verify_saved and (
                preflight["allowed_network"] != args.scope
                or preflight["detected_network"] != args.scope
                or preflight["network_warning"]
                or not preflight["scanner_available"]
            ):
                raise RuntimeError("Scan preflight no longer matches the authorised home scope")
            print(
                json.dumps(
                    {
                        "preflight": {
                            key: preflight[key]
                            for key in (
                                "allowed_network",
                                "scanner_version",
                                "ai_model",
                                "ai_available",
                                "mdns_enabled",
                            )
                        }
                    }
                ),
                flush=True,
            )
            for profile in ("light", "deep"):
                page = context.new_page()
                if args.verify_saved:
                    scan_id = saved_ids[profile]
                    page.goto(base + f"/scans/{scan_id}", wait_until="domcontentloaded")
                    scans[profile] = {
                        "id": scan_id,
                        "page": page,
                        "finished": True,
                        "refreshed": None,
                    }
                    continue
                page.on(
                    "dialog",
                    lambda dialog: (
                        dialog.accept()
                        if dialog.type == "confirm" and args.scope in dialog.message
                        else dialog.dismiss()
                    ),
                )
                page.goto(base + "/" + profile)
                if profile == "deep":
                    page.locator("#deepHostInput").fill(args.host)
                expect(page.locator("#scanLaunchButton")).to_be_enabled(timeout=60000)
                with page.expect_response(
                    lambda response: (
                        response.request.method == "POST"
                        and response.url.endswith("/api/live-scans")
                    ),
                    timeout=60000,
                ) as launch:
                    page.locator("#scanLaunchButton").click()
                if launch.value.status != 202:
                    save(run, profile + "-submission-error.json", launch.value.json())
                    raise RuntimeError(f"{profile} submission returned HTTP {launch.value.status}")
                scan_id = launch.value.json()["scan_id"]
                save(run, profile + "-id.json", {"scan_id": scan_id})
                scans[profile] = {
                    "id": scan_id,
                    "page": page,
                    "start": time.monotonic(),
                    "finished": False,
                    "refreshed": False,
                    "last": None,
                    "timeline": [],
                }
                print(json.dumps({"started": profile, "scan_id": scan_id}), flush=True)
            started = time.monotonic()
            while not all(item["finished"] for item in scans.values()):
                if time.monotonic() - started > 3000:
                    raise TimeoutError(
                        "Live review deadline; preserve the saved IDs, never resubmit"
                    )
                for profile, item in scans.items():
                    if item["finished"]:
                        continue
                    response = read_api(context, base + f"/api/live-scans/{item['id']}/progress")
                    if not response.ok:
                        raise RuntimeError(f"{profile} progress returned HTTP {response.status}")
                    progress = response.json()
                    stamp = {
                        key: progress.get(key)
                        for key in ("state", "phase", "coverage", "analysis_progress")
                    }
                    elapsed = round(time.monotonic() - item["start"], 1)
                    if stamp != item["last"]:
                        item["timeline"].append({"elapsed_s": elapsed, **stamp})
                        save(run, profile + "-timeline.json", item["timeline"])
                        print(
                            json.dumps(
                                {
                                    "profile": profile,
                                    "elapsed_s": elapsed,
                                    "state": progress["state"],
                                    "phase": progress["phase"],
                                    "completed": progress["coverage"]["service_completed_count"],
                                    "analysis": progress.get("analysis_progress"),
                                }
                            ),
                            flush=True,
                        )
                        item["last"] = stamp
                    if not item["refreshed"] and progress["phase"] != "finished":
                        item["page"].reload()
                        expect(item["page"].locator("#scanProgress")).to_be_visible(timeout=60000)
                        expect(item["page"].locator("#scanLaunchButton")).to_be_disabled()
                        if profile == "deep":
                            expect(item["page"].locator("#deepHostInput")).to_have_value(args.host)
                        if item["page"].evaluate(
                            "document.documentElement.scrollWidth > innerWidth"
                        ):
                            errors.append(profile + " progress has horizontal page overflow")
                        item["refreshed"] = True
                    if progress["phase"] == "finished":
                        item["finished"] = True
                        report = read_api(context, base + f"/api/live-scans/{item['id']}").json()
                        save(run, profile + "-report.json", report)
                        print(
                            json.dumps(
                                {
                                    "finished": profile,
                                    "elapsed_s": elapsed,
                                    "state": report["state"],
                                    "devices": len(report["devices"]),
                                    "open_services": sum(
                                        service["state"] == "open" for service in report["services"]
                                    ),
                                    "findings": len(report["findings"]),
                                    "error_count": len(report["errors"]),
                                    "warning_count": len(report["warnings"]),
                                }
                            ),
                            flush=True,
                        )
                welcome.wait_for_timeout(5000)
            flow_results = {
                "mode": "saved_reports" if args.verify_saved else "live_scans",
                "scan_submissions": len(submissions),
                "refresh_kept_both_jobs": None
                if args.verify_saved
                else all(item["refreshed"] for item in scans.values()),
                "automatic_reports_after_analysis": None if args.verify_saved else True,
            }
            save(run, "scan-flow-results.json", flow_results)
            for profile, item in scans.items():
                page = item["page"]
                expect(page).to_have_url(base + f"/scans/{item['id']}", timeout=60000)
                expect(page.locator("#report-content")).to_have_attribute(
                    "data-reading-ready", "true", timeout=60000
                )
                for width in (320, 390, 768, 1440):
                    page.set_viewport_size({"width": width, "height": 900})
                    if page.evaluate("document.documentElement.scrollWidth > innerWidth"):
                        errors.append(f"{profile} report overflow at {width}px")
                    page.evaluate("window.scrollTo(0, 0)")
                    page.screenshot(path=str(run / f"{profile}-{width}-viewport.png"))
                    page.screenshot(path=str(run / f"{profile}-{width}.png"), full_page=True)
                    if profile == "deep" and width == 390:
                        page.locator("#device-summaries").screenshot(
                            path=str(run / "deep-device-card-390.png")
                        )
                (run / (profile + "-report-text.txt")).write_text(
                    page.locator("body").inner_text(), encoding="utf-8"
                )
                expect(page.locator("#changes-overview")).not_to_be_empty()
                expect(page.locator("#shareReportButton")).to_be_enabled()
                page.locator("#feature-inventory > summary").click()
                expect(page.locator("#feature-inventory-list")).not_to_be_empty()
                page.locator("#shareReportButton").click()
                expect(page.locator("#report-export-dialog")).to_be_visible()
                expect(page.locator("#report-export-dialog .report-export-preview")).to_be_visible(
                    timeout=60000
                )
                page.get_by_role("button", name="Close preview", exact=True).click()
            inventory = read_api(context, base + "/api/devices?limit=24")
            if not inventory.ok:
                raise RuntimeError("The live saved-device inventory could not be read")
            inventory_data = inventory.json()
            inventory_views = {}
            for view in ("favourites", "not-recognised", "unfinished", "review"):
                response = read_api(context, base + f"/api/devices?limit=24&view={view}")
                if not response.ok or response.json().get("view") != view:
                    raise RuntimeError("The saved-device API did not confirm an applied view")
                inventory_views[view] = response.json()["total"]
            device_page = context.new_page()
            navigation = device_page.goto(base + "/devices")
            if navigation is None or not navigation.ok:
                raise RuntimeError("The live saved-device page could not be opened")
            expect(device_page.locator("#device-library-status")).to_contain_text(
                "Page", timeout=60000
            )
            device_page.get_by_role("combobox", name="Show saved devices").select_option(
                "favourites"
            )
            device_page.get_by_role("button", name="Search devices", exact=True).click()
            expect(device_page.locator("#device-library-empty")).to_be_visible(timeout=60000)
            device_page.get_by_role("button", name="Reset search and view", exact=True).click()
            expect(device_page.locator("#device-library-applied")).to_contain_text(
                "Applied view: All devices.", timeout=60000
            )
            expect(device_page.locator("#device-library-list")).to_have_attribute(
                "aria-busy", "false", timeout=60000
            )
            expect(device_page.locator("#device-library-status")).to_contain_text(
                "Page", timeout=60000
            )
            device_page.get_by_role("combobox", name="Show saved devices").select_option("review")
            device_page.get_by_role("button", name="Search devices", exact=True).click()
            # A visible card may still belong to the previous view. Wait for the
            # applied filter and completed load before opening its disclosures.
            expect(device_page.locator("#device-library-applied")).to_contain_text(
                "Applied view: With items to review.", timeout=60000
            )
            expect(device_page.locator("#device-library-list")).to_have_attribute(
                "aria-busy", "false", timeout=60000
            )
            card = device_page.locator(".device-library-card").first
            expect(card).to_be_visible(timeout=60000)
            return_key = card.get_attribute("data-device-key")
            card.locator(".device-library-history > summary").click()
            card.get_by_role("link").first.click()
            expect(device_page.locator("#report-content")).to_have_attribute(
                "data-reading-ready", "true", timeout=60000
            )
            device_page.get_by_role("link", name="My devices", exact=True).click()
            expect(device_page.get_by_role("combobox", name="Show saved devices")).to_have_value(
                "review"
            )
            expect(card).to_have_attribute("data-device-key", return_key)
            device_page.bring_to_front()
            expect(card.locator(".device-library-primary h3")).to_be_focused(timeout=20000)
            device_page.close()
            monitor = read_api(context, base + "/api/monitoring")
            if monitor.status != 404:
                raise RuntimeError("The removed periodic-check API must not be available")
            save(
                run,
                "feature-verification.json",
                {
                    "inventory_total": inventory_data["total"],
                    "inventory_warnings": inventory_data["warnings"],
                    "inventory_view_counts": inventory_views,
                    "inventory_filter_browser_reset": True,
                    "inventory_report_return_context": True,
                    "private_exports_opened": 2,
                    "comparison_and_feature_sections_present": True,
                    "periodic_checks_removed": True,
                },
            )
            browser_results = {
                **flow_results,
                "page_errors": errors,
            }
            save(run, "browser-results.json", browser_results)
            browser.close()
            browser = context = None
        after = hashes(normal_root / "scans")
        integrity = {
            "normal_existing_reports_unchanged": all(
                after.get(name) == digest for name, digest in before.items()
            )
        }
        if args.verify_saved:
            integrity["saved_test_evidence_unchanged"] = saved_before == hashes(data / "scans")
        save(run, "integrity.json", integrity)
        require_review_success(browser_results, integrity, saved_only=args.verify_saved)
        print(
            "SAVED_REPORT_REVIEW_COMPLETE" if args.verify_saved else "LIVE_SCAN_PAIR_COMPLETE",
            flush=True,
        )
    except Exception as error:
        save(
            run,
            "failed-browser-results.json",
            {"page_errors": errors, "submissions": len(submissions)},
        )
        save(run, "check-failure.json", {"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        # Only this helper's own backend is stopped. Normal PID/port remains untouched.
        if process is not None and process.poll() is None:
            if cancel_headers and any(not item["finished"] for item in scans.values()):
                for item in scans.values():
                    if item["finished"]:
                        continue
                    try:
                        request = urllib.request.Request(
                            base + f"/api/live-scans/{item['id']}",
                            data=b"{}",
                            headers=cancel_headers,
                            method="DELETE",
                        )
                        with urllib.request.urlopen(request, timeout=10):
                            pass
                    except Exception:
                        pass  # Confirm actual active jobs below; never assume a cancellation.
            safe_to_stop = not scans
            if cancel_headers:
                until = time.monotonic() + 45
                while time.monotonic() < until:
                    try:
                        request = urllib.request.Request(
                            base + "/api/running-scans", headers=cancel_headers
                        )
                        with urllib.request.urlopen(request, timeout=5) as response:
                            if not json.load(response)["items"]:
                                safe_to_stop = True
                                break
                    except Exception:
                        break
                    time.sleep(1)
            if not safe_to_stop:
                save(
                    run,
                    "cleanup.json",
                    {
                        "owned_backend_stopped": False,
                        "pid": process.pid,
                        "port": port,
                        "reason": "Active job cleanup could not be confirmed; backend kept alive.",
                    },
                )
                print(
                    "Owned test backend left alive; inspect cleanup.json before another run.",
                    flush=True,
                )
            else:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
                save(run, "cleanup.json", {"owned_backend_stopped": True, "pid": process.pid})


if __name__ == "__main__":
    main()
