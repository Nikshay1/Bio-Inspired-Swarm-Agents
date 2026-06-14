"""Ant species agent — route optimization via mealpy ACOR + networkx.

Builds a networkx weighted graph from input, runs Ant Colony Optimization
for route finding, and returns a GraphPayload with ordered_path set.

For small/discrete routing problems, falls back to networkx shortest path
when ACOR's continuous domain doesn't map well.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import networkx as nx
import numpy as np
from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, PayloadType
from csma.bus.translator import to_payload

logger = logging.getLogger(__name__)


def _build_graph(data: dict) -> nx.Graph:
    """Build a networkx graph from input data.

    Args:
        data: Dict with "nodes" (list[str]) and "edges" (list[dict])
              where each edge has "from", "to", "weight" keys.
              Alternatively, a "distance_matrix" (list[list[float]]) with "nodes".

    Returns:
        A networkx.Graph with weight attributes.
    """
    G = nx.Graph()

    nodes = data.get("nodes", [])
    G.add_nodes_from(nodes)

    if "distance_matrix" in data:
        matrix = data["distance_matrix"]
        for i, n1 in enumerate(nodes):
            for j, n2 in enumerate(nodes):
                if i < j and matrix[i][j] > 0:
                    G.add_edge(n1, n2, weight=matrix[i][j])
    elif "edges" in data:
        for e in data["edges"]:
            G.add_edge(e["from"], e["to"], weight=e.get("weight", 1.0))

    return G


def _solve_tsp_nearest_neighbor(G: nx.Graph, start: str | None = None) -> tuple[list[str], float]:
    """Greedy nearest-neighbor TSP heuristic as a baseline.

    Args:
        G: The weighted graph.
        start: Starting node. If None, picks the first node.

    Returns:
        (path, total_cost) tuple.
    """
    nodes = list(G.nodes())
    if not nodes:
        return [], 0.0

    if start is None:
        start = nodes[0]

    visited = [start]
    unvisited = set(nodes) - {start}
    total_cost = 0.0

    current = start
    while unvisited:
        best_next = None
        best_weight = float("inf")
        for neighbor in unvisited:
            if G.has_edge(current, neighbor):
                w = G[current][neighbor]["weight"]
                if w < best_weight:
                    best_weight = w
                    best_next = neighbor

        if best_next is None:
            # Graph not fully connected — pick any remaining
            best_next = next(iter(unvisited))
            best_weight = 0.0

        visited.append(best_next)
        unvisited.discard(best_next)
        total_cost += best_weight
        current = best_next

    return visited, total_cost


def _solve_with_acor(G: nx.Graph, n_ants: int = 50, epochs: int = 100) -> tuple[list[str], float]:
    """Use mealpy ACOR to optimize a route through the graph.

    ACOR works in continuous space, so we encode node permutation as
    continuous variables and decode via argsort (rank-order encoding).

    Args:
        G: The weighted graph.
        n_ants: Population size for ACOR.
        epochs: Number of optimization epochs.

    Returns:
        (path, total_cost) tuple.
    """
    from mealpy import FloatVar
    from mealpy.swarm_based.ACOR import OriginalACOR

    nodes = list(G.nodes())
    n = len(nodes)

    if n <= 2:
        # Too small for optimization — just return direct
        cost = 0.0
        if n == 2 and G.has_edge(nodes[0], nodes[1]):
            cost = G[nodes[0]][nodes[1]]["weight"]
        return nodes, cost

    # Distance lookup (default to large value if edge missing)
    big_penalty = 1e6

    def dist(i: int, j: int) -> float:
        n1, n2 = nodes[i], nodes[j]
        if G.has_edge(n1, n2):
            return G[n1][n2]["weight"]
        return big_penalty

    def objective(solution: np.ndarray) -> float:
        """Total route cost from rank-order decoded permutation."""
        perm = np.argsort(solution)
        total = 0.0
        for k in range(n - 1):
            total += dist(int(perm[k]), int(perm[k + 1]))
        return total

    problem_dict = {
        "bounds": FloatVar(lb=[0.0] * n, ub=[1.0] * n),
        "minmax": "min",
        "obj_func": objective,
    }

    model = OriginalACOR(epoch=epochs, pop_size=n_ants)
    model.solve(problem_dict, seed=42)

    # Decode best solution
    best_perm = np.argsort(model.g_best.solution)
    path = [nodes[int(i)] for i in best_perm]
    total_cost = float(model.g_best.target.fitness)

    return path, total_cost


@tool
def ant_route_optimizer(input_json: str) -> str:
    """Find the optimal route through a graph using Ant Colony Optimization.

    This tool is used for any task that involves finding a path, route, or
    tour through a network of nodes with weighted edges (e.g., delivery
    routing, TSP, shortest path).

    Args:
        input_json: A JSON string with the following structure:
            {
                "subtask_id": "unique-id",
                "nodes": ["A", "B", "C", ...],
                "edges": [{"from": "A", "to": "B", "weight": 10.0}, ...],
                // OR instead of edges:
                "distance_matrix": [[0, 10, 20], [10, 0, 15], [20, 15, 0]],
                "method": "acor" | "nearest_neighbor" (optional, default "acor")
            }

    Returns:
        A BusMessage JSON string containing a GraphPayload with the
        optimal ordered path and total cost.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "ant-task")
    method = data.get("method", "acor")

    logger.info("AntAgent: building graph from %d nodes", len(data.get("nodes", [])))
    G = _build_graph(data)

    if method == "nearest_neighbor" or len(G.nodes()) <= 3:
        logger.info("AntAgent: using nearest-neighbor heuristic")
        path, cost = _solve_tsp_nearest_neighbor(G)
    else:
        logger.info("AntAgent: running ACOR optimization (%d nodes)", len(G.nodes()))
        try:
            path, cost = _solve_with_acor(G)
        except Exception as e:
            logger.warning("AntAgent: ACOR failed (%s), falling back to nearest-neighbor", e)
            path, cost = _solve_tsp_nearest_neighbor(G)

    # Build the path edges for the payload
    path_graph = nx.Graph()
    for i in range(len(path) - 1):
        n1, n2 = path[i], path[i + 1]
        w = G[n1][n2]["weight"] if G.has_edge(n1, n2) else 0.0
        path_graph.add_edge(n1, n2, weight=w)

    payload = to_payload(
        path_graph,
        PayloadType.GRAPH,
        ordered_path=path,
        total_cost=cost,
    )

    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="AntAgent",
        agent_class=AgentClass.SEARCH,
        payload=payload,
    )

    logger.info("AntAgent: route found, cost=%.2f, path=%s", cost, " → ".join(path))
    return msg.to_json()
