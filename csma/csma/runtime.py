"""CSMA runtime — public entrypoint.

run_csma(problem: str) -> str
    Instantiates the Deep Agent and invokes it on the problem,
    returning the final synthesized answer.
"""

from __future__ import annotations

import logging

from csma.config import setup_logging
from csma.orchestrator.deep_agent import build_csma_agent

logger = logging.getLogger(__name__)


def run_csma(problem: str) -> str:
    """Run the CSMA multi-agent system on a problem.

    This is the single public entrypoint.  It:
    1. Sets up logging
    2. Builds the Deep Agent (with all subagents)
    3. Invokes the agent on the problem
    4. Extracts and returns the final answer

    Args:
        problem: A natural-language description of the problem to solve.
                 Should contain enough detail for the orchestrator to
                 decompose into typed subtasks.

    Returns:
        The synthesized final answer as a string.
    """
    setup_logging()
    logger.info("=" * 60)
    logger.info("CSMA: Starting problem decomposition")
    logger.info("=" * 60)
    logger.info("Problem: %s", problem[:200] + ("..." if len(problem) > 200 else ""))

    agent = build_csma_agent()

    logger.info("CSMA: Invoking Deep Agent")
    result = agent.invoke({
        "messages": [{"role": "user", "content": problem}],
    })

    # Extract the final answer from the agent's response.
    # AIMessage.content can be a str OR a list of content blocks
    # (e.g. [{"type": "text", "text": "..."}]).
    final_message = result["messages"][-1]
    raw_content = final_message.content if hasattr(final_message, "content") else str(final_message)

    if isinstance(raw_content, list):
        # Structured content blocks — extract text parts
        parts = []
        for block in raw_content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        answer = "\n".join(parts)
    else:
        answer = str(raw_content)

    logger.info("=" * 60)
    logger.info("CSMA: Completed — answer length=%d chars", len(answer))
    logger.info("=" * 60)

    return answer
