"""Ecosystem Bus — translator between raw library output and typed payloads.

Two pure functions:
- to_payload():  raw mealpy/networkx result → typed Payload
- payload_to_context():  any Payload → clean natural-language for LLM

This is the wrapper that turns a meaningless solution vector into a
structured graph or ranking, and then renders it back into text that
a reasoning LLM can consume with no information loss.
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from csma.bus.schema import (
    FeatureStreamsPayload,
    GraphPayload,
    Payload,
    PayloadType,
    RankedOption,
    RankedOptionsPayload,
    TextPayload,
)


# ---------------------------------------------------------------------------
# raw library output → typed Payload
# ---------------------------------------------------------------------------

def to_payload(raw: Any, kind: PayloadType, **kwargs: Any) -> Payload:
    """Convert a raw mealpy/networkx result into a typed Payload.

    Args:
        raw: The raw result from the library.  Shape depends on ``kind``:
            - GRAPH: a networkx.Graph (with 'weight' edge attr) + optional
              ``ordered_path`` kwarg (list[str]).
            - RANKED_OPTIONS: a list of dicts with keys
              ``{"name": str, "score": float, "rationale": str|None}``.
            - TEXT: a plain string.
            - FEATURE_STREAMS: a dict[str, list[float]].
        kind: Which payload type to produce.
        **kwargs: Extra fields forwarded to the payload constructor.
            For GRAPH: ``ordered_path``, ``total_cost``.
            For RANKED_OPTIONS: ``confidence``.

    Returns:
        A fully validated Payload instance.

    Raises:
        ValueError: If ``kind`` is not recognized or ``raw`` has wrong shape.
    """
    if kind == PayloadType.GRAPH:
        return _graph_from_raw(raw, **kwargs)
    elif kind == PayloadType.RANKED_OPTIONS:
        return _ranked_from_raw(raw, **kwargs)
    elif kind == PayloadType.TEXT:
        return TextPayload(content=str(raw))
    elif kind == PayloadType.FEATURE_STREAMS:
        if not isinstance(raw, dict):
            raise ValueError(
                f"FEATURE_STREAMS expects dict[str, list[float]], got {type(raw)}"
            )
        return FeatureStreamsPayload(channels=raw)
    else:
        raise ValueError(f"Unknown payload kind: {kind}")


def _graph_from_raw(
    raw: Any,
    ordered_path: list[str] | None = None,
    total_cost: float | None = None,
    **_kwargs: Any,
) -> GraphPayload:
    """Build a GraphPayload from a networkx Graph or a dict representation."""
    if isinstance(raw, nx.Graph):
        nodes = [str(n) for n in raw.nodes()]
        edges = [
            {
                "from": str(u),
                "to": str(v),
                "weight": float(d.get("weight", 1.0)),
            }
            for u, v, d in raw.edges(data=True)
        ]
        if total_cost is None:
            total_cost = sum(e["weight"] for e in edges)
    elif isinstance(raw, dict):
        nodes = raw.get("nodes", [])
        edges = raw.get("edges", [])
        if total_cost is None:
            total_cost = raw.get("total_cost", sum(e.get("weight", 0) for e in edges))
    else:
        raise ValueError(f"GRAPH expects nx.Graph or dict, got {type(raw)}")

    return GraphPayload(
        nodes=nodes,
        edges=edges,
        total_cost=total_cost,
        ordered_path=ordered_path,
    )


def _ranked_from_raw(
    raw: Any,
    confidence: float = 1.0,
    **_kwargs: Any,
) -> RankedOptionsPayload:
    """Build a RankedOptionsPayload from a list of option dicts."""
    if not isinstance(raw, list) or len(raw) == 0:
        raise ValueError(
            f"RANKED_OPTIONS expects non-empty list of dicts, got {type(raw)}"
        )

    options = []
    for item in raw:
        if isinstance(item, dict):
            options.append(
                RankedOption(
                    name=str(item["name"]),
                    score=float(item["score"]),
                    rationale=item.get("rationale"),
                )
            )
        elif isinstance(item, RankedOption):
            options.append(item)
        else:
            raise ValueError(f"Unexpected option type: {type(item)}")

    # Sort descending by score
    options.sort(key=lambda o: o.score, reverse=True)
    winner = options[0].name

    return RankedOptionsPayload(
        options=options,
        winner=winner,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# typed Payload → natural-language context for LLM
# ---------------------------------------------------------------------------

def payload_to_context(payload: Payload) -> str:
    """Render any Payload into clean natural-language context for an LLM.

    Designed for no information loss:
    - Graph → enumerated edge list + total cost + ordered path (if set)
    - Ranking → scored list with winner flagged
    - Text → content as-is
    - Streams → channel summary (kept separate)

    Args:
        payload: A validated Payload instance.

    Returns:
        A human-readable string suitable for LLM context injection.
    """
    if isinstance(payload, GraphPayload):
        return _context_graph(payload)
    elif isinstance(payload, RankedOptionsPayload):
        return _context_ranked(payload)
    elif isinstance(payload, TextPayload):
        return payload.content
    elif isinstance(payload, FeatureStreamsPayload):
        return _context_streams(payload)
    else:
        return str(payload)


def _context_graph(p: GraphPayload) -> str:
    """Render a GraphPayload as readable context."""
    lines = [f"Graph Result (total cost: {p.total_cost:.2f})"]

    if p.ordered_path:
        lines.append(f"Optimal path: {' → '.join(p.ordered_path)}")

    lines.append(f"Nodes ({len(p.nodes)}): {', '.join(p.nodes)}")
    lines.append(f"Edges ({len(p.edges)}):")
    for i, e in enumerate(p.edges, 1):
        lines.append(f"  {i}. {e['from']} → {e['to']}  (weight: {e['weight']:.2f})")

    return "\n".join(lines)


def _context_ranked(p: RankedOptionsPayload) -> str:
    """Render a RankedOptionsPayload as readable context."""
    lines = [
        f"Decision Result (confidence: {p.confidence:.0%})",
        f"Winner: {p.winner}",
        "Rankings:",
    ]
    for i, opt in enumerate(p.options, 1):
        flag = " ★ WINNER" if opt.name == p.winner else ""
        rationale = f" — {opt.rationale}" if opt.rationale else ""
        lines.append(f"  {i}. {opt.name} (score: {opt.score:.4f}){rationale}{flag}")

    return "\n".join(lines)


def _context_streams(p: FeatureStreamsPayload) -> str:
    """Render a FeatureStreamsPayload as readable context."""
    lines = [f"Feature Streams ({len(p.channels)} channels, kept separate):"]
    for name, values in p.channels.items():
        preview = ", ".join(f"{v:.4f}" for v in values[:5])
        suffix = f", ... ({len(values)} total)" if len(values) > 5 else ""
        lines.append(f"  • {name}: [{preview}{suffix}]")
    return "\n".join(lines)
