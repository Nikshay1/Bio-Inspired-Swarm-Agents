"""End-to-end integration test for CSMA.

Tests the full decompose → route → execute → synthesize pipeline.
Requires either a live LLM API key (reads from .env) or can be skipped.
"""

import json
import os

import pytest

from csma.bus.schema import BusMessage, GraphPayload, RankedOptionsPayload


# ---------------------------------------------------------------------------
# Unit-level integration: species tools work together
# ---------------------------------------------------------------------------

class TestSpeciesIntegration:
    """Test that ant + bee species tools produce compatible BusMessages."""

    def test_ant_and_bee_produce_compatible_messages(self):
        """Both tools produce BusMessages that can be collected and rendered."""
        from csma.species.ant import ant_route_optimizer
        from csma.species.bee import bee_consensus_optimizer
        from csma.bus.translator import payload_to_context

        # Run ant
        ant_input = {
            "subtask_id": "route",
            "nodes": ["A", "B", "C"],
            "edges": [
                {"from": "A", "to": "B", "weight": 10},
                {"from": "B", "to": "C", "weight": 15},
                {"from": "A", "to": "C", "weight": 25},
            ],
            "method": "nearest_neighbor",
        }
        ant_result = ant_route_optimizer.invoke(json.dumps(ant_input))
        ant_msg = BusMessage.from_json(ant_result)

        # Run bee
        bee_input = {
            "subtask_id": "partner",
            "options": [
                {"name": "DHL", "scores": {"cost": 0.8, "speed": 0.7}},
                {"name": "FedEx", "scores": {"cost": 0.6, "speed": 0.9}},
            ],
            "criteria": [
                {"name": "cost", "weight": 2.0},
                {"name": "speed", "weight": 1.0},
            ],
        }
        bee_result = bee_consensus_optimizer.invoke(json.dumps(bee_input))
        bee_msg = BusMessage.from_json(bee_result)

        # Both should be renderable
        ant_context = payload_to_context(ant_msg.payload)
        bee_context = payload_to_context(bee_msg.payload)

        assert "A" in ant_context or "B" in ant_context
        assert "DHL" in bee_context or "FedEx" in bee_context

    def test_render_bus_messages_context(self):
        """render_bus_messages_context combines multiple results."""
        from csma.species.ant import ant_route_optimizer
        from csma.species.bee import bee_consensus_optimizer
        from csma.orchestrator.deep_agent import render_bus_messages_context

        ant_result = ant_route_optimizer.invoke(json.dumps({
            "subtask_id": "r",
            "nodes": ["X", "Y"],
            "edges": [{"from": "X", "to": "Y", "weight": 5}],
            "method": "nearest_neighbor",
        }))

        bee_result = bee_consensus_optimizer.invoke(json.dumps({
            "subtask_id": "p",
            "options": [{"name": "A", "scores": {"q": 0.9}}],
            "criteria": [{"name": "q", "weight": 1.0}],
        }))

        context = render_bus_messages_context([ant_result, bee_result])
        assert "AntAgent" in context
        assert "BeeAgent" in context
        assert "Result 1" in context
        assert "Result 2" in context


# ---------------------------------------------------------------------------
# Full orchestrator test (requires LLM API key)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
    reason="No LLM API key configured — skipping live orchestrator test",
)
class TestFullOrchestrator:
    """Full end-to-end test with live LLM (skipped if no API key)."""

    def test_delivery_planning(self):
        """The full CSMA pipeline produces a non-empty answer."""
        from csma.runtime import run_csma

        problem = (
            "Find the optimal delivery route across 3 cities "
            "(A, B, C) with distances A-B=10, B-C=15, A-C=25. "
            "Then choose between DHL (cost=0.8, speed=0.7) and "
            "FedEx (cost=0.6, speed=0.9) with criteria: cost (weight=2), "
            "speed (weight=1). Finally, write a one-sentence summary."
        )

        answer = run_csma(problem)
        assert isinstance(answer, str)
        assert len(answer) > 10
