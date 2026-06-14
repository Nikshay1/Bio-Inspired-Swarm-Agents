"""Tests for Ecosystem Bus translator — to_payload() and payload_to_context()."""

import pytest
import networkx as nx

from csma.bus.schema import (
    FeatureStreamsPayload,
    GraphPayload,
    PayloadType,
    RankedOption,
    RankedOptionsPayload,
    TextPayload,
)
from csma.bus.translator import payload_to_context, to_payload


# ---------------------------------------------------------------------------
# to_payload — GRAPH
# ---------------------------------------------------------------------------

class TestToPayloadGraph:
    """to_payload(raw, GRAPH) from networkx and dict inputs."""

    def test_from_networkx_graph(self):
        G = nx.Graph()
        G.add_edge("A", "B", weight=10.0)
        G.add_edge("B", "C", weight=20.0)

        payload = to_payload(G, PayloadType.GRAPH, ordered_path=["A", "B", "C"])
        assert isinstance(payload, GraphPayload)
        assert set(payload.nodes) == {"A", "B", "C"}
        assert len(payload.edges) == 2
        assert payload.total_cost == 30.0
        assert payload.ordered_path == ["A", "B", "C"]

    def test_from_networkx_no_path(self):
        G = nx.Graph()
        G.add_edge("X", "Y", weight=5.0)

        payload = to_payload(G, PayloadType.GRAPH)
        assert isinstance(payload, GraphPayload)
        assert payload.ordered_path is None
        assert payload.total_cost == 5.0

    def test_from_dict(self):
        raw = {
            "nodes": ["A", "B"],
            "edges": [{"from": "A", "to": "B", "weight": 7.5}],
            "total_cost": 7.5,
        }
        payload = to_payload(raw, PayloadType.GRAPH)
        assert isinstance(payload, GraphPayload)
        assert payload.total_cost == 7.5

    def test_from_dict_auto_cost(self):
        raw = {
            "nodes": ["A", "B"],
            "edges": [{"from": "A", "to": "B", "weight": 3.0}],
        }
        payload = to_payload(raw, PayloadType.GRAPH)
        assert payload.total_cost == 3.0

    def test_explicit_total_cost_override(self):
        G = nx.Graph()
        G.add_edge("A", "B", weight=10.0)

        payload = to_payload(G, PayloadType.GRAPH, total_cost=999.0)
        assert payload.total_cost == 999.0

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="GRAPH expects"):
            to_payload("not a graph", PayloadType.GRAPH)


# ---------------------------------------------------------------------------
# to_payload — RANKED_OPTIONS
# ---------------------------------------------------------------------------

class TestToPayloadRanked:
    """to_payload(raw, RANKED_OPTIONS) from list of dicts."""

    def test_basic_ranking(self):
        raw = [
            {"name": "DHL", "score": 0.7, "rationale": "Cheap"},
            {"name": "FedEx", "score": 0.9, "rationale": "Fast"},
        ]
        payload = to_payload(raw, PayloadType.RANKED_OPTIONS, confidence=0.85)
        assert isinstance(payload, RankedOptionsPayload)
        assert payload.winner == "FedEx"  # highest score
        assert payload.confidence == 0.85
        assert payload.options[0].score > payload.options[1].score

    def test_sorts_descending(self):
        raw = [
            {"name": "C", "score": 0.1},
            {"name": "A", "score": 0.9},
            {"name": "B", "score": 0.5},
        ]
        payload = to_payload(raw, PayloadType.RANKED_OPTIONS)
        assert [o.name for o in payload.options] == ["A", "B", "C"]

    def test_rationale_optional(self):
        raw = [{"name": "X", "score": 1.0}]
        payload = to_payload(raw, PayloadType.RANKED_OPTIONS)
        assert payload.options[0].rationale is None

    def test_from_ranked_option_objects(self):
        raw = [RankedOption(name="Z", score=0.5)]
        payload = to_payload(raw, PayloadType.RANKED_OPTIONS)
        assert payload.winner == "Z"

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="non-empty list"):
            to_payload([], PayloadType.RANKED_OPTIONS)

    def test_wrong_type_raises(self):
        with pytest.raises(ValueError, match="non-empty list"):
            to_payload("bad", PayloadType.RANKED_OPTIONS)


# ---------------------------------------------------------------------------
# to_payload — TEXT
# ---------------------------------------------------------------------------

class TestToPayloadText:
    """to_payload(raw, TEXT) from a string."""

    def test_basic_text(self):
        payload = to_payload("Hello world", PayloadType.TEXT)
        assert isinstance(payload, TextPayload)
        assert payload.content == "Hello world"

    def test_non_string_coerced(self):
        payload = to_payload(42, PayloadType.TEXT)
        assert payload.content == "42"


# ---------------------------------------------------------------------------
# to_payload — FEATURE_STREAMS
# ---------------------------------------------------------------------------

class TestToPayloadStreams:
    """to_payload(raw, FEATURE_STREAMS) from a dict."""

    def test_basic_streams(self):
        raw = {"ch1": [1.0, 2.0], "ch2": [3.0]}
        payload = to_payload(raw, PayloadType.FEATURE_STREAMS)
        assert isinstance(payload, FeatureStreamsPayload)
        assert payload.channels == raw

    def test_wrong_type_raises(self):
        with pytest.raises(ValueError, match="FEATURE_STREAMS expects"):
            to_payload([1, 2], PayloadType.FEATURE_STREAMS)


# ---------------------------------------------------------------------------
# payload_to_context
# ---------------------------------------------------------------------------

class TestPayloadToContext:
    """payload_to_context() produces readable strings for all payload types."""

    def test_graph_context(self):
        payload = GraphPayload(
            nodes=["A", "B", "C"],
            edges=[
                {"from": "A", "to": "B", "weight": 10.0},
                {"from": "B", "to": "C", "weight": 5.0},
            ],
            total_cost=15.0,
            ordered_path=["A", "B", "C"],
        )
        ctx = payload_to_context(payload)
        assert "15.00" in ctx
        assert "A → B → C" in ctx
        assert "A → B" in ctx  # edge listing
        assert "B → C" in ctx

    def test_graph_context_no_path(self):
        payload = GraphPayload(
            nodes=["X"], edges=[], total_cost=0.0
        )
        ctx = payload_to_context(payload)
        assert "Optimal path" not in ctx
        assert "0.00" in ctx

    def test_ranked_context(self):
        payload = RankedOptionsPayload(
            options=[
                RankedOption(name="DHL", score=0.9, rationale="Cheapest"),
                RankedOption(name="FedEx", score=0.7),
            ],
            winner="DHL",
            confidence=0.85,
        )
        ctx = payload_to_context(payload)
        assert "DHL" in ctx
        assert "WINNER" in ctx
        assert "85%" in ctx
        assert "Cheapest" in ctx

    def test_text_context(self):
        payload = TextPayload(content="Summary goes here.")
        ctx = payload_to_context(payload)
        assert ctx == "Summary goes here."

    def test_streams_context(self):
        payload = FeatureStreamsPayload(
            channels={
                "vision": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                "audio": [1.0],
            }
        )
        ctx = payload_to_context(payload)
        assert "vision" in ctx
        assert "audio" in ctx
        assert "kept separate" in ctx.lower()
        assert "6 total" in ctx  # truncated
