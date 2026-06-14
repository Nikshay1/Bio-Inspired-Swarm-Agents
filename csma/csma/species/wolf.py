"""Wolf species agent — consensus with authority weighting via mealpy GWO.

Phase 3: Grey Wolf Optimizer with explicit authority/priority among options.
Same output type as Bee (RankedOptionsPayload), but biases toward options
held by higher-authority decision makers.

Currently a STUB — returns a placeholder result.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, RankedOptionsPayload, RankedOption

logger = logging.getLogger(__name__)


@tool
def wolf_authority_optimizer(input_json: str) -> str:
    """Choose among options with authority/priority weighting using Grey Wolf Optimizer.

    Use this when there are explicit authority levels or priorities among
    decision-makers — NOT for equal-weight options (use bee for that).

    STUB: Phase 3 implementation pending.

    Args:
        input_json: JSON string with "subtask_id", "options", "criteria",
                    and "authority_weights".

    Returns:
        A BusMessage JSON with RankedOptionsPayload.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "wolf-task")
    options = data.get("options", [])

    logger.warning("WolfAgent: STUB — returning placeholder ranking")

    ranked = [
        RankedOption(name=o.get("name", f"opt-{i}"), score=0.5, rationale="STUB")
        for i, o in enumerate(options)
    ]
    winner = ranked[0].name if ranked else "none"

    payload = RankedOptionsPayload(options=ranked, winner=winner, confidence=0.0)
    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="WolfAgent",
        agent_class=AgentClass.CONSENSUS,
        payload=payload,
    )
    return msg.to_json()
