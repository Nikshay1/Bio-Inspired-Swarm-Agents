"""Crow species agent — creative problem-solving via mealpy CSA + LLM.

Phase 3: Crow Search Algorithm drives exploration over solution strategies,
then an LLM renders the creative output under constraints.
Returns a TextPayload.

Currently a STUB — returns a placeholder result.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, TextPayload

logger = logging.getLogger(__name__)


@tool
def crow_creative_solver(input_json: str) -> str:
    """Generate creative solutions under constraints using Crow Search Algorithm.

    Use this for creative generation tasks where the output must satisfy
    specific constraints — NOT for straightforward planning (use LLM directly).

    STUB: Phase 3 implementation pending.

    Args:
        input_json: JSON string with "subtask_id", "task", "constraints".

    Returns:
        A BusMessage JSON with TextPayload.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "crow-task")
    task = data.get("task", "")

    logger.warning("CrowAgent: STUB — returning placeholder text")

    payload = TextPayload(content=f"[STUB] Crow creative output for: {task}")
    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="CrowAgent",
        agent_class=AgentClass.REASONING,
        payload=payload,
    )
    return msg.to_json()
