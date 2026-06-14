"""Tests for Ecosystem Bus schema — BusMessage round-trip and payload discrimination."""

import pytest

from csma.bus.schema import (
    AgentClass,
    BusMessage,
    FeatureStreamsPayload,
    GraphPayload,
    PayloadType,
    RankedOption,
    RankedOptionsPayload,
    TextPayload,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_graph_msg() -> BusMessage:
    return BusMessage(
        subtask_id="task-001",
        source_agent="AntAgent",
        agent_class=AgentClass.SEARCH,
        payload=GraphPayload(
            nodes=["A", "B", "C", "D"],
            edges=[
                {"from": "A", "to": "B", "weight": 10.0},
                {"from": "B", "to": "C", "weight": 15.5},
                {"from": "C", "to": "D", "weight": 7.2},
            ],
            total_cost=32.7,
            ordered_path=["A", "B", "C", "D"],
        ),
    )


def _make_ranked_msg() -> BusMessage:
    return BusMessage(
        subtask_id="task-002",
        source_agent="BeeAgent",
        agent_class=AgentClass.CONSENSUS,
        payload=RankedOptionsPayload(
            options=[
                RankedOption(name="DHL", score=0.85, rationale="Cheapest"),
                RankedOption(name="FedEx", score=0.72, rationale="Fast"),
                RankedOption(name="BlueDart", score=0.60),
            ],
            winner="DHL",
            confidence=0.85,
        ),
    )


def _make_text_msg() -> BusMessage:
    return BusMessage(
        subtask_id="task-003",
        source_agent="HumanAgent",
        agent_class=AgentClass.REASONING,
        payload=TextPayload(content="The optimal route is A→B→C→D."),
    )


def _make_streams_msg() -> BusMessage:
    return BusMessage(
        subtask_id="task-004",
        source_agent="OctopusAgent",
        agent_class=AgentClass.PROCESSING,
        payload=FeatureStreamsPayload(
            channels={
                "arm_1": [0.1, 0.2, 0.3],
                "arm_2": [0.4, 0.5, 0.6],
            }
        ),
    )


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

class TestBusMessageRoundTrip:
    """BusMessage.from_json(msg.to_json()) must restore the correct subclass."""

    def test_graph_payload_round_trip(self):
        original = _make_graph_msg()
        json_str = original.to_json()
        restored = BusMessage.from_json(json_str)

        assert isinstance(restored.payload, GraphPayload)
        assert restored.payload.type == PayloadType.GRAPH
        assert restored.payload.nodes == original.payload.nodes
        assert restored.payload.edges == original.payload.edges
        assert restored.payload.total_cost == original.payload.total_cost
        assert restored.payload.ordered_path == original.payload.ordered_path
        assert restored.source_agent == "AntAgent"
        assert restored.agent_class == AgentClass.SEARCH

    def test_ranked_options_payload_round_trip(self):
        original = _make_ranked_msg()
        json_str = original.to_json()
        restored = BusMessage.from_json(json_str)

        assert isinstance(restored.payload, RankedOptionsPayload)
        assert restored.payload.type == PayloadType.RANKED_OPTIONS
        assert len(restored.payload.options) == 3
        assert restored.payload.winner == "DHL"
        assert restored.payload.confidence == 0.85
        assert restored.payload.options[0].name == "DHL"
        assert restored.payload.options[2].rationale is None

    def test_text_payload_round_trip(self):
        original = _make_text_msg()
        json_str = original.to_json()
        restored = BusMessage.from_json(json_str)

        assert isinstance(restored.payload, TextPayload)
        assert restored.payload.type == PayloadType.TEXT
        assert restored.payload.content == "The optimal route is A→B→C→D."

    def test_feature_streams_payload_round_trip(self):
        original = _make_streams_msg()
        json_str = original.to_json()
        restored = BusMessage.from_json(json_str)

        assert isinstance(restored.payload, FeatureStreamsPayload)
        assert restored.payload.type == PayloadType.FEATURE_STREAMS
        assert set(restored.payload.channels.keys()) == {"arm_1", "arm_2"}
        assert restored.payload.channels["arm_1"] == [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestBusMessageEdgeCases:
    """Edge cases for BusMessage serialization."""

    def test_graph_no_ordered_path(self):
        msg = BusMessage(
            subtask_id="t",
            source_agent="SlimeMoldAgent",
            agent_class=AgentClass.SEARCH,
            payload=GraphPayload(
                nodes=["X"], edges=[], total_cost=0.0, ordered_path=None
            ),
        )
        restored = BusMessage.from_json(msg.to_json())
        assert restored.payload.ordered_path is None

    def test_empty_edges_list(self):
        msg = BusMessage(
            subtask_id="t",
            source_agent="AntAgent",
            agent_class=AgentClass.SEARCH,
            payload=GraphPayload(nodes=["A"], edges=[], total_cost=0.0),
        )
        restored = BusMessage.from_json(msg.to_json())
        assert restored.payload.edges == []

    def test_empty_streams(self):
        msg = BusMessage(
            subtask_id="t",
            source_agent="OctopusAgent",
            agent_class=AgentClass.PROCESSING,
            payload=FeatureStreamsPayload(channels={}),
        )
        restored = BusMessage.from_json(msg.to_json())
        assert restored.payload.channels == {}

    def test_message_id_auto_generated(self):
        msg = _make_text_msg()
        assert len(msg.message_id) > 0
        # UUID format: 8-4-4-4-12
        assert msg.message_id.count("-") == 4

    def test_timestamp_auto_set(self):
        msg = _make_text_msg()
        assert msg.timestamp > 0

    def test_meta_default_empty(self):
        msg = _make_text_msg()
        assert msg.meta == {}

    def test_meta_preserved(self):
        msg = BusMessage(
            subtask_id="t",
            source_agent="AntAgent",
            agent_class=AgentClass.SEARCH,
            payload=GraphPayload(nodes=[], edges=[], total_cost=0.0),
            meta={"debug": True, "iteration": 42},
        )
        restored = BusMessage.from_json(msg.to_json())
        assert restored.meta["debug"] is True
        assert restored.meta["iteration"] == 42

    def test_ranked_options_empty_rationale(self):
        msg = BusMessage(
            subtask_id="t",
            source_agent="BeeAgent",
            agent_class=AgentClass.CONSENSUS,
            payload=RankedOptionsPayload(
                options=[RankedOption(name="A", score=1.0)],
                winner="A",
                confidence=1.0,
            ),
        )
        restored = BusMessage.from_json(msg.to_json())
        assert restored.payload.options[0].rationale is None
