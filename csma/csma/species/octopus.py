"""Octopus species agent — hub-and-arms parallel processing.

Phase 3: Hub fans out to arm coroutines that act locally then report.
Returns a FeatureStreamsPayload (channels kept separate).

Currently a STUB — returns a placeholder result.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, FeatureStreamsPayload

logger = logging.getLogger(__name__)


@tool
def octopus_parallel_processor(input_json: str) -> str:
    """Process multiple independent streams with local intelligence per arm.

    Use for tasks with locally intelligent, independent sub-streams that
    need a central hub for coordination.

    STUB: Phase 3 implementation pending.

    Args:
        input_json: JSON string with "subtask_id", "streams".

    Returns:
        A BusMessage JSON with FeatureStreamsPayload.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "octopus-task")

    logger.warning("OctopusAgent: STUB — returning placeholder streams")

    payload = FeatureStreamsPayload(channels={"stub_arm": [0.0]})
    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="OctopusAgent",
        agent_class=AgentClass.PROCESSING,
        payload=payload,
    )
    return msg.to_json()
