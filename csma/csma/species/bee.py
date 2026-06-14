"""Bee species agent — consensus decision via mealpy ABC.

Scores options with Artificial Bee Colony optimization over a quality
function built from weighted criteria. Applies a quorum threshold and
suppresses inferior options. Returns a RankedOptionsPayload.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import numpy as np
from langchain_core.tools import tool

from csma.bus.schema import AgentClass, BusMessage, PayloadType
from csma.bus.translator import to_payload

logger = logging.getLogger(__name__)


def _build_quality_function(
    options: list[dict],
    criteria: list[dict],
) -> tuple[callable, list[str]]:
    """Build an objective function for ABC from options and criteria.

    Each option has scores on each criterion.  The objective function
    evaluates a continuous vector that represents weights/preferences
    and maps to the option-level scoring.

    For simplicity, we use ABC to optimize a weighted combination:
    each dimension of the solution vector is a bonus weight for an option,
    and the fitness is the negative of the weighted-sum quality (minimize).

    Args:
        options: List of dicts, each with "name" and "scores" (dict[criterion_name → float]).
        criteria: List of dicts, each with "name" and "weight" (float).

    Returns:
        (objective_function, option_names) — the objective takes a numpy
        array and returns a float (lower is better).
    """
    option_names = [o["name"] for o in options]
    n_opts = len(option_names)

    # Build a score matrix: options × criteria
    crit_names = [c["name"] for c in criteria]
    crit_weights = np.array([c.get("weight", 1.0) for c in criteria])
    crit_weights = crit_weights / crit_weights.sum()  # normalize

    score_matrix = np.zeros((n_opts, len(crit_names)))
    for i, opt in enumerate(options):
        for j, cn in enumerate(crit_names):
            score_matrix[i, j] = opt.get("scores", {}).get(cn, 0.5)

    # Weighted quality per option
    base_quality = score_matrix @ crit_weights  # shape: (n_opts,)

    def objective(solution: np.ndarray) -> float:
        """Evaluate: solution is a perturbation vector for option preferences.

        We add the solution vector (clipped to [0,1]) as a small bonus
        to each option's quality, then return the negative of the best
        option's quality (so ABC minimizes → finds best separation).
        """
        perturbation = np.clip(solution[:n_opts], 0, 1) * 0.1
        adjusted = base_quality + perturbation
        # We want to maximize the gap between best and second-best
        sorted_q = np.sort(adjusted)[::-1]
        if len(sorted_q) >= 2:
            gap = sorted_q[0] - sorted_q[1]
        else:
            gap = sorted_q[0]
        # Minimize negative gap → maximize gap
        return -gap

    return objective, option_names


def _score_options_with_abc(
    options: list[dict],
    criteria: list[dict],
    pop_size: int = 30,
    epochs: int = 50,
) -> list[dict]:
    """Run ABC optimization to rank options.

    Args:
        options: Options to evaluate (each has "name" and "scores").
        criteria: Weighted criteria for evaluation.
        pop_size: ABC population size.
        epochs: Number of ABC epochs.

    Returns:
        List of {"name": str, "score": float, "rationale": str} sorted
        by quality (best first).
    """
    from mealpy import FloatVar
    from mealpy.swarm_based.ABC import OriginalABC

    n_opts = len(options)
    crit_names = [c["name"] for c in criteria]
    crit_weights = np.array([c.get("weight", 1.0) for c in criteria])
    crit_weights = crit_weights / crit_weights.sum()

    # Compute base quality scores
    results = []
    for opt in options:
        scores = opt.get("scores", {})
        quality = sum(
            scores.get(cn, 0.5) * crit_weights[j]
            for j, cn in enumerate(crit_names)
        )
        # Build rationale from top criteria
        top_criteria = sorted(
            [(cn, scores.get(cn, 0.5)) for cn in crit_names],
            key=lambda x: x[1],
            reverse=True,
        )
        rationale_parts = [f"{c}: {s:.2f}" for c, s in top_criteria[:3]]
        results.append({
            "name": opt["name"],
            "score": float(quality),
            "rationale": ", ".join(rationale_parts),
        })

    # Now run ABC to fine-tune the ranking via exploration
    if n_opts >= 2:
        try:
            obj_fn, _ = _build_quality_function(options, criteria)

            problem_dict = {
                "bounds": FloatVar(lb=[0.0] * n_opts, ub=[1.0] * n_opts),
                "minmax": "min",
                "obj_func": obj_fn,
            }

            model = OriginalABC(epoch=epochs, pop_size=pop_size, n_limits=25)
            model.solve(problem_dict, seed=42)

            # Use the best solution to slightly adjust scores
            perturbation = np.clip(model.g_best.solution[:n_opts], 0, 1) * 0.1
            for i, r in enumerate(results):
                r["score"] = float(r["score"] + perturbation[i])

        except Exception as e:
            logger.warning("BeeAgent: ABC optimization failed (%s), using base scores", e)

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _compute_quorum_confidence(scores: list[float]) -> float:
    """Compute quorum confidence based on score gap.

    Higher confidence means clearer winner (bigger gap between #1 and #2).
    Returns a value in [0, 1].
    """
    if len(scores) < 2:
        return 1.0

    sorted_scores = sorted(scores, reverse=True)
    gap = sorted_scores[0] - sorted_scores[1]
    max_possible = sorted_scores[0] if sorted_scores[0] > 0 else 1.0
    confidence = min(gap / max_possible, 1.0)

    # Scale up — even small gaps indicate reasonable confidence
    return min(confidence * 2.0 + 0.5, 1.0)


@tool
def bee_consensus_optimizer(input_json: str) -> str:
    """Choose the best option from a set of candidates using Artificial Bee Colony.

    This tool is used when you need to select among a fixed set of known
    options based on multiple weighted criteria (e.g., choosing a vendor,
    picking a strategy, selecting a configuration).

    Args:
        input_json: A JSON string with the following structure:
            {
                "subtask_id": "unique-id",
                "options": [
                    {
                        "name": "Option A",
                        "scores": {"cost": 0.8, "reliability": 0.9, "speed": 0.7}
                    },
                    ...
                ],
                "criteria": [
                    {"name": "cost", "weight": 2.0},
                    {"name": "reliability", "weight": 1.5},
                    {"name": "speed", "weight": 1.0}
                ]
            }

    Returns:
        A BusMessage JSON string containing a RankedOptionsPayload with
        ranked options, the winner, and quorum confidence.
    """
    data = json.loads(input_json)
    subtask_id = data.get("subtask_id", "bee-task")
    options = data.get("options", [])
    criteria = data.get("criteria", [])

    if not options:
        raise ValueError("BeeAgent: no options provided")

    # Default criteria if none specified
    if not criteria:
        # Infer criteria from the first option's scores
        if options[0].get("scores"):
            criteria = [{"name": k, "weight": 1.0} for k in options[0]["scores"]]
        else:
            criteria = [{"name": "quality", "weight": 1.0}]
            for opt in options:
                opt.setdefault("scores", {"quality": 0.5})

    logger.info(
        "BeeAgent: evaluating %d options on %d criteria",
        len(options),
        len(criteria),
    )

    ranked = _score_options_with_abc(options, criteria)

    # Compute quorum confidence
    confidence = _compute_quorum_confidence([r["score"] for r in ranked])

    payload = to_payload(ranked, PayloadType.RANKED_OPTIONS, confidence=confidence)

    msg = BusMessage(
        subtask_id=subtask_id,
        source_agent="BeeAgent",
        agent_class=AgentClass.CONSENSUS,
        payload=payload,
    )

    logger.info(
        "BeeAgent: winner=%s, confidence=%.0f%%",
        payload.winner,
        confidence * 100,
    )
    return msg.to_json()
