"""Tests for ant species tool — route optimization."""

import json

import pytest

from csma.bus.schema import AgentClass, BusMessage, GraphPayload


class TestAntRouteTool:
    """Unit tests for ant_route_optimizer."""

    def test_small_graph_nearest_neighbor(self):
        """Ant tool returns valid BusMessage with GraphPayload for a small graph."""
        from csma.species.ant import ant_route_optimizer

        input_data = {
            "subtask_id": "test-ant-001",
            "nodes": ["A", "B", "C"],
            "edges": [
                {"from": "A", "to": "B", "weight": 10.0},
                {"from": "B", "to": "C", "weight": 15.0},
                {"from": "A", "to": "C", "weight": 25.0},
            ],
            "method": "nearest_neighbor",
        }

        result_json = ant_route_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)

        assert isinstance(msg.payload, GraphPayload)
        assert msg.source_agent == "AntAgent"
        assert msg.agent_class == AgentClass.SEARCH
        assert msg.subtask_id == "test-ant-001"
        assert msg.payload.ordered_path is not None
        assert len(msg.payload.ordered_path) == 3
        assert set(msg.payload.ordered_path) == {"A", "B", "C"}
        assert msg.payload.total_cost > 0

    def test_distance_matrix_input(self):
        """Ant tool accepts distance_matrix format."""
        from csma.species.ant import ant_route_optimizer

        input_data = {
            "subtask_id": "test-ant-002",
            "nodes": ["X", "Y", "Z"],
            "distance_matrix": [
                [0, 5, 10],
                [5, 0, 7],
                [10, 7, 0],
            ],
            "method": "nearest_neighbor",
        }

        result_json = ant_route_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)

        assert isinstance(msg.payload, GraphPayload)
        assert msg.payload.ordered_path is not None
        assert len(msg.payload.ordered_path) == 3
        assert msg.payload.total_cost > 0

    def test_acor_optimization(self):
        """Ant tool runs ACOR on a medium graph (4+ nodes)."""
        from csma.species.ant import ant_route_optimizer

        input_data = {
            "subtask_id": "test-ant-003",
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                {"from": "A", "to": "B", "weight": 10.0},
                {"from": "A", "to": "C", "weight": 20.0},
                {"from": "A", "to": "D", "weight": 30.0},
                {"from": "B", "to": "C", "weight": 15.0},
                {"from": "B", "to": "D", "weight": 25.0},
                {"from": "C", "to": "D", "weight": 5.0},
            ],
            "method": "acor",
        }

        result_json = ant_route_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)

        assert isinstance(msg.payload, GraphPayload)
        assert msg.payload.ordered_path is not None
        assert len(msg.payload.ordered_path) == 4
        assert set(msg.payload.ordered_path) == {"A", "B", "C", "D"}

    def test_output_is_valid_bus_message_json(self):
        """The tool output can be round-tripped through BusMessage."""
        from csma.species.ant import ant_route_optimizer

        input_data = {
            "subtask_id": "test-roundtrip",
            "nodes": ["P", "Q"],
            "edges": [{"from": "P", "to": "Q", "weight": 42.0}],
            "method": "nearest_neighbor",
        }

        result_json = ant_route_optimizer.invoke(json.dumps(input_data))

        # Must be valid JSON
        parsed = json.loads(result_json)
        assert "payload" in parsed
        assert "source_agent" in parsed

        # Must round-trip
        msg = BusMessage.from_json(result_json)
        msg2 = BusMessage.from_json(msg.to_json())
        assert msg2.payload.total_cost == msg.payload.total_cost
