"""Scoped event-loop diagnostics; never suppress errors or record request secrets."""

import logging
from contextlib import contextmanager

from app.schemas.common import iso_z, utc_now

logger = logging.getLogger(__name__)


@contextmanager
def observe_asyncio_errors(loop):
    previous = loop.get_exception_handler()
    diagnostics = {"count": 0, "last_event": None}

    def handler(current_loop, context):
        error = context.get("exception")
        callback = getattr(context.get("handle"), "_callback", None)
        # Names and error codes only: no repr(handle), arguments, URL or peer address.
        event = {
            "at": iso_z(utc_now()),
            "exception": type(error).__name__ if error else "unknown",
            "winerror": getattr(error, "winerror", None),
            "callback": getattr(callback, "__qualname__", "unknown"),
        }
        diagnostics["count"] += 1
        diagnostics["last_event"] = event
        logger.warning("Asyncio lifecycle diagnostic: %s", event)
        if previous:
            previous(current_loop, context)
        else:
            current_loop.default_exception_handler(context)

    loop.set_exception_handler(handler)
    try:
        yield diagnostics
    finally:
        if loop.get_exception_handler() is handler:
            loop.set_exception_handler(previous)
