"""Mantis species agent — multi-headed parallel feature processing.

Phase 3: N parallel feature heads that process independent dimensions
of a problem. Channels are kept strictly separate.
Returns a FeatureStreamsPayload.

Currently a STUB — returns a placeholder result.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, FeatureStreamsPayload

logger = logging.getLogger(__name__)


@tool
def mantis_feature_processor(input_json: str) -> str:
    """Process multi-dimensional features with N parallel heads kept separate.

    Use when multiple feature dimensions must be processed independently
    without merging.

    STUB: Phase 3 implementation pending.

    Args:
        input_json: JSON string with "subtask_id", "features".

    Returns:
        A BusMessage JSON with FeatureStreamsPayload.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "mantis-task")

    logger.warning("MantisAgent: STUB — returning placeholder streams")

    payload = FeatureStreamsPayload(channels={"stub_head": [0.0]})
    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="MantisAgent",
        agent_class=AgentClass.PROCESSING,
        payload=payload,
    )
    return msg.to_json()
