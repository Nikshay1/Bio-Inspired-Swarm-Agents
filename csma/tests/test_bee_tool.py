"""Tests for bee species tool — consensus decision."""

import json

import pytest

from csma.bus.schema import AgentClass, BusMessage, RankedOptionsPayload


class TestBeeConsensusTool:
    """Unit tests for bee_consensus_optimizer."""

    def test_basic_ranking(self):
        """Bee tool returns valid BusMessage with ranked options."""
        from csma.species.bee import bee_consensus_optimizer

        input_data = {
            "subtask_id": "test-bee-001",
            "options": [
                {
                    "name": "DHL",
                    "scores": {"cost": 0.7, "reliability": 0.9, "speed": 0.8},
                },
                {
                    "name": "FedEx",
                    "scores": {"cost": 0.6, "reliability": 0.95, "speed": 0.9},
                },
                {
                    "name": "BlueDart",
                    "scores": {"cost": 0.85, "reliability": 0.7, "speed": 0.6},
                },
            ],
            "criteria": [
                {"name": "cost", "weight": 2.0},
                {"name": "reliability", "weight": 1.5},
                {"name": "speed", "weight": 1.0},
            ],
        }

        result_json = bee_consensus_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)

        assert isinstance(msg.payload, RankedOptionsPayload)
        assert msg.source_agent == "BeeAgent"
        assert msg.agent_class == AgentClass.CONSENSUS
        assert msg.subtask_id == "test-bee-001"
        assert len(msg.payload.options) == 3
        assert msg.payload.winner in {"DHL", "FedEx", "BlueDart"}
        assert 0.0 <= msg.payload.confidence <= 1.0

    def test_two_options(self):
        """Bee tool works with just two options."""
        from csma.species.bee import bee_consensus_optimizer

        input_data = {
            "subtask_id": "test-bee-002",
            "options": [
                {"name": "A", "scores": {"quality": 0.9}},
                {"name": "B", "scores": {"quality": 0.3}},
            ],
            "criteria": [{"name": "quality", "weight": 1.0}],
        }

        result_json = bee_consensus_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)

        assert isinstance(msg.payload, RankedOptionsPayload)
        assert msg.payload.winner == "A"
        # A has a much higher score, so confidence should be decent
        assert msg.payload.confidence > 0.0

    def test_options_sorted_by_score(self):
        """Options in the result are sorted by score (best first)."""
        from csma.species.bee import bee_consensus_optimizer

        input_data = {
            "subtask_id": "test-bee-003",
            "options": [
                {"name": "Low", "scores": {"q": 0.1}},
                {"name": "High", "scores": {"q": 0.9}},
                {"name": "Mid", "scores": {"q": 0.5}},
            ],
            "criteria": [{"name": "q", "weight": 1.0}],
        }

        result_json = bee_consensus_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)

        scores = [o.score for o in msg.payload.options]
        assert scores == sorted(scores, reverse=True)

    def test_default_criteria_inference(self):
        """When no criteria are provided, bee infers from option scores."""
        from csma.species.bee import bee_consensus_optimizer

        input_data = {
            "subtask_id": "test-bee-004",
            "options": [
                {"name": "X", "scores": {"a": 0.8, "b": 0.6}},
                {"name": "Y", "scores": {"a": 0.5, "b": 0.9}},
            ],
        }

        result_json = bee_consensus_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)
        assert isinstance(msg.payload, RankedOptionsPayload)
        assert msg.payload.winner in {"X", "Y"}

    def test_output_is_valid_bus_message_json(self):
        """The tool output can be round-tripped through BusMessage."""
        from csma.species.bee import bee_consensus_optimizer

        input_data = {
            "subtask_id": "test-roundtrip",
            "options": [
                {"name": "A", "scores": {"q": 0.5}},
                {"name": "B", "scores": {"q": 0.5}},
            ],
            "criteria": [{"name": "q", "weight": 1.0}],
        }

        result_json = bee_consensus_optimizer.invoke(json.dumps(input_data))

        # Must be valid JSON
        parsed = json.loads(result_json)
        assert "payload" in parsed

        # Must round-trip
        msg = BusMessage.from_json(result_json)
        msg2 = BusMessage.from_json(msg.to_json())
        assert msg2.payload.winner == msg.payload.winner
