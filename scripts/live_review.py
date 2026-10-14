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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import detect_private_network, load_config  # noqa: E402
from app.scanner.network import connection_snapshot  # noqa: E402
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


def normal_public_check(run):
    """Inspect served code, not another instance's private session or reports."""
    result = {"reachable": False}
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/openapi.json", timeout=5) as response:
            schema = json.load(response)
        result.update(
            reachable=True,
            deletion_route="/api/reports/delete" in schema["paths"],
            restore_route="/api/reports/restore" in schema["paths"],
            recovery_route="/api/reports/recovery" in schema["paths"],
            capabilities_route="/api/report-capabilities" in schema["paths"],
        )
        mismatches = []
        for path in (ROOT / "app/static").rglob("*"):
            if path.is_file() and path.suffix in {".js", ".mjs", ".css"}:
                route = "/static/" + path.relative_to(ROOT / "app/static").as_posix()
                with urllib.request.urlopen("http://127.0.0.1:8765" + route, timeout=5) as reply:
                    if reply.read() != path.read_bytes():
                        mismatches.append(route)
        result["asset_mismatches"] = mismatches
    except Exception as error:
        result["error_type"] = type(error).__name__
    save(run, "normal-public-check.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorised", action="store_true")
    parser.add_argument("--scope", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--artifacts", required=True, type=Path)
    args = parser.parse_args()
    if not args.authorised:
        parser.error("Live scans require an explicit --authorised opt-in")
    run = args.artifacts.resolve()
    if not run.is_relative_to(ROOT / ".test-artifacts") or run.exists():
        parser.error("Use a new private folder under .test-artifacts; never reuse scan IDs")
    config = load_config()
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
    data = run / "data"
    data.mkdir()
    settings_path = normal_root / "settings.json"
    saved = (
        Settings.model_validate_json(settings_path.read_bytes())
        if settings_path.exists()
        else Settings()
    )
    save(run, "normal-settings-facts.json", saved.model_dump())
    # Keep name discovery enabled as configured, but do not call optional Pi-hole.
    # Use the verified current automatic scope, without changing normal settings.
    isolated = saved.model_copy(
        update={
            "allowed_network": None,
            "interface": None,
            "retain_raw_xml": True,
            "pihole_enabled": False,
        }
    )
    save(data, "settings.json", isolated.model_dump(mode="json"))
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
        from playwright.sync_api import expect, sync_playwright

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
            welcome.goto(bootstrap)
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
            if (
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
                    page.screenshot(path=str(run / f"{profile}-{width}.png"), full_page=True)
                (run / (profile + "-report-text.txt")).write_text(
                    page.locator("body").inner_text(), encoding="utf-8"
                )
            save(
                run,
                "browser-results.json",
                {
                    "page_errors": errors,
                    "scan_submissions": len(submissions),
                    "refresh_kept_both_jobs": all(item["refreshed"] for item in scans.values()),
                    "automatic_reports_after_analysis": True,
                },
            )
            browser.close()
            browser = context = None
            if len(submissions) != 2:
                raise RuntimeError("Unexpected additional scan submission")
        after = hashes(normal_root / "scans")
        save(
            run,
            "integrity.json",
            {
                "normal_existing_reports_unchanged": all(
                    after.get(name) == digest for name, digest in before.items()
                )
            },
        )
        print("LIVE_SCAN_PAIR_COMPLETE", flush=True)
    except Exception as error:
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
