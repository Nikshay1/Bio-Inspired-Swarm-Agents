"""Elephant species agent — consensus with experience weighting via mealpy EHO.

Phase 3: Elephant Herding Optimization with experience/history-based weighting.
Same output type as Bee (RankedOptionsPayload), but biases decisions based
on historical outcomes and accumulated experience.

Currently a STUB — returns a placeholder result.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, RankedOptionsPayload, RankedOption

logger = logging.getLogger(__name__)


@tool
def elephant_experience_optimizer(input_json: str) -> str:
    """Choose among options using experience/history weighting via Elephant Herding.

    Use this when decision history or accumulated experience should
    influence the choice — NOT for equal-weight or authority-based decisions.

    STUB: Phase 3 implementation pending.

    Args:
        input_json: JSON string with "subtask_id", "options", "criteria",
                    and "history".

    Returns:
        A BusMessage JSON with RankedOptionsPayload.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "elephant-task")
    options = data.get("options", [])

    logger.warning("ElephantAgent: STUB — returning placeholder ranking")

    ranked = [
        RankedOption(name=o.get("name", f"opt-{i}"), score=0.5, rationale="STUB")
        for i, o in enumerate(options)
    ]
    winner = ranked[0].name if ranked else "none"

    payload = RankedOptionsPayload(options=ranked, winner=winner, confidence=0.0)
    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="ElephantAgent",
        agent_class=AgentClass.CONSENSUS,
        payload=payload,
    )
    return msg.to_json()
