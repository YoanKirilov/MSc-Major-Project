"""Bounded synthetic-only diagnostics. Raw traces never enter the upload folder."""

import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

MAX_TRACE_BYTES = 30 * 1024 * 1024
MAX_JOB_BYTES = 100 * 1024 * 1024


def redact(value, secrets):
    for secret in sorted(secrets, key=len, reverse=True):
        if secret:
            value = value.replace(secret, "[redacted]")
    return value


def safe_trace(source, destination, secrets):
    """Rewrite archive entries in memory; never extract paths or copy raw secrets."""
    if source.stat().st_size > MAX_TRACE_BYTES:
        return False
    with ZipFile(source) as incoming:
        entries = incoming.infolist()
        if len(entries) > 10000 or sum(item.file_size for item in entries) > MAX_TRACE_BYTES:
            return False
        with ZipFile(destination, "w", ZIP_DEFLATED) as outgoing:
            for item in entries:
                if item.filename.startswith(("/", "\\")) or ".." in Path(item.filename).parts:
                    raise ValueError("Unsafe trace entry")
                payload = incoming.read(item)
                for secret in secrets:
                    if secret:
                        payload = payload.replace(secret.encode(), b"[redacted]")
                outgoing.writestr(item.filename, payload)
    return True


def capture(context, folder, index, secrets):
    """Best effort only; a diagnostic failure must not replace the test failure."""
    for number, page in enumerate(context.pages[:2]):
        try:
            mask = [page.locator('input[type="password"], input[name*="token" i]')]
            if secrets:
                mask.append(
                    page.get_by_text(re.compile("|".join(re.escape(s) for s in secrets if s)))
                )
            page.screenshot(
                path=str(folder / f"context-{index}-page-{number}.png"), mask=mask, timeout=3000
            )
        except Exception:
            pass
    try:
        context.tracing.stop(path=str(folder / f"context-{index}.zip"))
    except Exception:
        pass
