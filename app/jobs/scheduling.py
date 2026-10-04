"""Bounded queue waits and execution budgets that do not charge waiting jobs."""

import asyncio
from contextlib import asynccontextmanager
from time import monotonic


class QueueExpired(Exception):
    pass


class QueueCancelled(Exception):
    pass


@asynccontextmanager
async def capacity_slot(capacity, *, timeout_s=3600, cancel_event=None):
    deadline = monotonic() + timeout_s
    acquired = False
    try:
        while not acquired:
            if cancel_event is not None and cancel_event.is_set():
                raise QueueCancelled
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise QueueExpired
            try:
                await asyncio.wait_for(capacity.acquire(), min(remaining, 0.25))
                acquired = True
            except TimeoutError:
                continue
        if cancel_event is not None and cancel_event.is_set():
            raise QueueCancelled
        yield
    finally:
        if acquired:
            capacity.release()


class ExecutionBudget:
    """Charge elapsed time only while at least one of this job's workers is active."""

    def __init__(self, seconds):
        self.remaining = seconds
        self.active = 0
        self.started = None

    @asynccontextmanager
    async def run(self):
        now = monotonic()
        if self.active:
            self.remaining -= now - self.started
        self.started = now
        if self.remaining <= 0:
            raise TimeoutError("Active execution budget exhausted")
        self.active += 1
        try:
            async with asyncio.timeout(max(0, self.remaining)):
                yield
        finally:
            now = monotonic()
            self.remaining -= now - self.started
            self.started = now
            self.active -= 1
