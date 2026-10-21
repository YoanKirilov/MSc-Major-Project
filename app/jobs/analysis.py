"""Analysis-stage coordination, separate from scanner orchestration."""

import asyncio
import logging

from app.jobs.scheduling import QueueExpired, capacity_slot
from app.schemas.scan import AnalysisProgress

logger = logging.getLogger(__name__)


async def execute_analysis(
    *, scan_id, service, capacity, checkpoint, finish, queue_timeout_s, timeout_s
):
    try:
        await checkpoint(
            scan_id,
            lambda current: current.model_copy(
                update={
                    "analysis_progress": (
                        current.analysis_progress or AnalysisProgress()
                    ).model_copy(update={"state": "waiting", "active": 0})
                }
            ),
        )
        async with capacity_slot(capacity, timeout_s=queue_timeout_s):
            async with asyncio.timeout(timeout_s):
                await service.explain_scan(scan_id)
    except QueueExpired:
        await finish(scan_id, warning_code="AI_QUEUE_EXPIRED")
    except asyncio.CancelledError:
        await finish(scan_id, warning_code="AI_EXPLANATION_CANCELLED")
        raise
    except Exception:
        logger.exception("AI explanation failed for scan %s", scan_id)
        await finish(scan_id, warning_code="AI_EXPLANATION_FAILED")
    else:
        await finish(scan_id)
