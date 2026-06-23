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

    def test_start_node_enforced(self):
        """Ant tool respects start_node — route must begin at the specified city."""
        from csma.species.ant import ant_route_optimizer

        input_data = {
            "subtask_id": "test-start-node",
            "nodes": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad"],
            "distance_matrix": [
                [   0, 1400, 980, 1330, 2050, 710],
                [1400,    0, 2150, 2180, 1530, 1550],
                [ 980, 2150,    0,  350, 1870,  570],
                [1330, 2180,  350,    0, 1660,  630],
                [2050, 1530, 1870, 1660,    0, 1490],
                [ 710, 1550,  570,  630, 1490,    0],
            ],
            "start_node": "Mumbai",
            "method": "acor",
        }

        result_json = ant_route_optimizer.invoke(json.dumps(input_data))
        msg = BusMessage.from_json(result_json)

        assert isinstance(msg.payload, GraphPayload)
        assert msg.payload.ordered_path is not None
        assert len(msg.payload.ordered_path) == 6
        assert msg.payload.ordered_path[0] == "Mumbai", (
            f"Route must start at Mumbai, got {msg.payload.ordered_path[0]}"
        )
        assert set(msg.payload.ordered_path) == {
            "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad"
        }
        # Verify cost matches the actual path leg-by-leg
        matrix = input_data["distance_matrix"]
        cities = input_data["nodes"]
        path = msg.payload.ordered_path
        expected_cost = sum(
            matrix[cities.index(path[i])][cities.index(path[i + 1])]
            for i in range(len(path) - 1)
        )
        assert msg.payload.total_cost == expected_cost, (
            f"Reported cost {msg.payload.total_cost} != actual {expected_cost}"
        )

