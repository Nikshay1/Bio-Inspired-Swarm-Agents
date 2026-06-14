"""Assemble the top-level Deep Agent with biological subagents.

This is the orchestrator — almost no new code.  Deep Agents supplies:
- write_todos: decompose the problem into subtasks with dependencies
- task tool: spawn subagents with context isolation
- async subagents: parallelism for independent subtasks
- synthesis: final step collects all results

We only configure it with our four subagents and the synthesis prompt.
"""

from __future__ import annotations

import logging

from deepagents import create_deep_agent

from csma.bus.translator import payload_to_context
from csma.bus.schema import BusMessage
from csma.config import get_llm, get_settings
from csma.orchestrator.subagents import ALL_SUBAGENTS

logger = logging.getLogger(__name__)

# The main orchestrator system prompt
ORCHESTRATOR_PROMPT = """\
You are CSMA (Cross-Species Multi-Agent System) — a heterogeneous multi-agent
orchestrator that decomposes problems and routes subtasks to bio-inspired
specialist agents.

## Your Workflow

1. **DECOMPOSE**: Use `write_todos` to break the user's problem into subtasks
   with dependencies.  Label each subtask with its type:
   - [search] for routing, scheduling, graph optimization
   - [consensus] for choosing among known options
   - [reasoning] for planning, summarizing, creative writing
   - [processing] for parallel data streams

2. **DELEGATE**: For each subtask, use the `task` tool to delegate to the
   appropriate subagent:
   - search_agent: routing, graph optimization, TSP
   - consensus_agent: vendor/option selection, ranking
   - reasoning_agent: summaries, plans, creative text
   - processing_agent: parallel feature streams

   Run INDEPENDENT subtasks in PARALLEL (use async subagents).
   Subtasks with dependencies must wait for their prerequisites.

3. **SYNTHESIZE**: When all subtask results are collected (they will be
   BusMessage JSON strings), combine them into a single coherent final
   answer for the user.  Extract the key information from each BusMessage:
   - GraphPayload: the optimal path and total cost
   - RankedOptionsPayload: the winner and confidence
   - TextPayload: the content
   - FeatureStreamsPayload: the channel summaries

   Produce a clear, well-structured response that incorporates ALL
   subtask results.

## Important Rules
- Always use write_todos FIRST to plan your approach.
- Always delegate to subagents — don't solve subtasks yourself (except
  for final synthesis).
- Each subagent returns a BusMessage JSON — pass these as context to
  dependent subtasks.
- Log which subagent handled each subtask for auditability.
"""


def build_csma_agent():
    """Build and return the top-level CSMA Deep Agent.

    Returns:
        A configured Deep Agent ready to invoke on problems.
    """
    settings = get_settings()
    llm = get_llm()

    model_str = f"{settings.llm_provider}:{settings.llm_model}"
    logger.info("Building CSMA agent with model=%s", model_str)

    agent = create_deep_agent(
        model=model_str,
        system_prompt=ORCHESTRATOR_PROMPT,
        subagents=ALL_SUBAGENTS,
    )

    logger.info(
        "CSMA agent assembled: %d subagents registered",
        len(ALL_SUBAGENTS),
    )
    return agent


def render_bus_messages_context(messages_json: list[str]) -> str:
    """Helper: render a list of BusMessage JSON strings into LLM context.

    Used during synthesis to convert all collected subtask results into
    readable text the orchestrator can use.

    Args:
        messages_json: List of BusMessage JSON strings from subagents.

    Returns:
        A single string with all results rendered as context.
    """
    sections = []
    for i, json_str in enumerate(messages_json, 1):
        try:
            msg = BusMessage.from_json(json_str)
            context = payload_to_context(msg.payload)
            sections.append(
                f"--- Result {i} (from {msg.source_agent}, "
                f"class={msg.agent_class.value}) ---\n{context}"
            )
        except Exception as e:
            logger.warning("Failed to parse BusMessage %d: %s", i, e)
            sections.append(f"--- Result {i} (raw) ---\n{json_str}")

    return "\n\n".join(sections)
