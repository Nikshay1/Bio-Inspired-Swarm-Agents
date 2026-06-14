"""Ecosystem Bus — typed message schema.

All data that crosses between agents is a BusMessage wrapping a typed
payload, serialized to JSON so it travels cleanly through Deep Agents'
message channel / virtual filesystem.

This is the ONE part with no off-the-shelf equivalent.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentClass(str, Enum):
    """Abstract agent class — determines which subagent handles a subtask."""
    SEARCH = "search"
    CONSENSUS = "consensus"
    REASONING = "reasoning"
    PROCESSING = "processing"


class PayloadType(str, Enum):
    """Discriminator for the payload union type."""
    GRAPH = "graph"
    RANKED_OPTIONS = "ranked"
    TEXT = "text"
    FEATURE_STREAMS = "streams"


# ---------------------------------------------------------------------------
# Payload types
# ---------------------------------------------------------------------------

class GraphPayload(BaseModel):
    """Result from a graph/route search (Ant, SlimeMold).

    Represents either a single optimized path (ordered_path set)
    or a pruned network topology (ordered_path=None).
    """
    type: Literal[PayloadType.GRAPH] = PayloadType.GRAPH
    nodes: list[str]
    edges: list[dict]  # {"from": str, "to": str, "weight": float}
    total_cost: float
    ordered_path: list[str] | None = None  # set when a single route was requested


class RankedOption(BaseModel):
    """A single option with its optimization score and optional rationale."""
    name: str
    score: float
    rationale: str | None = None


class RankedOptionsPayload(BaseModel):
    """Result from a consensus/decision agent (Bee, Wolf, Elephant).

    Contains ranked options with a declared winner and quorum confidence.
    """
    type: Literal[PayloadType.RANKED_OPTIONS] = PayloadType.RANKED_OPTIONS
    options: list[RankedOption]
    winner: str
    confidence: float  # 0..1 quorum strength


class TextPayload(BaseModel):
    """Free-form text result (Human reasoning, Crow creative output)."""
    type: Literal[PayloadType.TEXT] = PayloadType.TEXT
    content: str


class FeatureStreamsPayload(BaseModel):
    """Multiple independent parallel data streams (Octopus, Starling, Mantis).

    Channels are kept SEPARATE — never merged.  Each key is a stream name,
    each value is the stream's feature vector.
    """
    type: Literal[PayloadType.FEATURE_STREAMS] = PayloadType.FEATURE_STREAMS
    channels: dict[str, list[float]]  # kept SEPARATE, never merged


# ---------------------------------------------------------------------------
# Discriminated union
# ---------------------------------------------------------------------------

Payload = Union[
    GraphPayload,
    RankedOptionsPayload,
    TextPayload,
    FeatureStreamsPayload,
]


# ---------------------------------------------------------------------------
# Bus message envelope
# ---------------------------------------------------------------------------

class BusMessage(BaseModel):
    """Envelope wrapping any typed payload for inter-agent communication.

    Every species tool returns one of these as a JSON string.  The
    orchestrator collects them and feeds them through payload_to_context()
    for synthesis.
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subtask_id: str
    source_agent: str  # e.g. "AntAgent"
    agent_class: AgentClass
    payload: Payload = Field(discriminator="type")
    timestamp: float = Field(default_factory=time.time)
    meta: dict = Field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to JSON string for transport."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, s: str) -> BusMessage:
        """Deserialize from JSON string, restoring correct payload subclass."""
        return cls.model_validate_json(s)
