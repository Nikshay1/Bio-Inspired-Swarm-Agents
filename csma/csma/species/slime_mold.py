"""SlimeMold species agent — network topology optimization via physarum flow.

Phase 2: Tero–Kobayashi–Nakagaki flow simulation on a networkx graph.
Iterates: pressures → flows → update conductivity → prune weak edges.
Returns a GraphPayload with ordered_path=None (topology only).

Currently a STUB — returns a minimal placeholder result.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, GraphPayload

logger = logging.getLogger(__name__)


@tool
def slime_mold_network_optimizer(input_json: str) -> str:
    """Optimize network topology using Physarum polycephalum (slime mold) simulation.

    Use this tool for network design problems where you need to find an
    efficient topology connecting multiple nodes — NOT for single-path routing
    (use ant_route_optimizer for that).

    STUB: Phase 2 implementation pending.

    Args:
        input_json: JSON string with "subtask_id", "nodes", "edges".

    Returns:
        A BusMessage JSON string with a GraphPayload (topology, no ordered_path).
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "slime-task")
    nodes = data.get("nodes", [])

    logger.warning("SlimeMoldAgent: STUB — returning placeholder topology")

    payload = GraphPayload(
        nodes=nodes,
        edges=[],
        total_cost=0.0,
        ordered_path=None,
    )
    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="SlimeMoldAgent",
        agent_class=AgentClass.SEARCH,
        payload=payload,
    )
    return msg.to_json()
