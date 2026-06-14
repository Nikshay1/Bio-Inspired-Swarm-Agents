"""Starling species agent — leaderless boids local rules.

Phase 3: Leaderless coordination via boids-like local rules for fast
reaction to distributed data streams.
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
def starling_swarm_processor(input_json: str) -> str:
    """Process streams using leaderless boids-like local coordination rules.

    Use for fast, leaderless reaction to distributed data — NOT for
    tasks requiring central coordination (use octopus for that).

    STUB: Phase 3 implementation pending.

    Args:
        input_json: JSON string with "subtask_id", "streams".

    Returns:
        A BusMessage JSON with FeatureStreamsPayload.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "starling-task")

    logger.warning("StarlingAgent: STUB — returning placeholder streams")

    payload = FeatureStreamsPayload(channels={"stub_flock": [0.0]})
    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="StarlingAgent",
        agent_class=AgentClass.PROCESSING,
        payload=payload,
    )
    return msg.to_json()
