# CSMA — Cross-Species Multi-Agent System

A heterogeneous multi-agent framework where each agent's algorithm is chosen by
which biological species evolved the best strategy for that subtask type.

## Architecture

```
User Problem
    │
    ▼
┌───────────────────────────────┐
│     Deep Agent Orchestrator    │  ← REUSED (deepagents)
│  ┌─────────────────────────┐  │
│  │   write_todos (planner) │  │  ← REUSED (deepagents)
│  │   Decompose → subtasks  │  │
│  └──────────┬──────────────┘  │
│             │ task tool        │  ← REUSED (deepagents)
│    ┌────────┼────────┐        │
│    ▼        ▼        ▼        │
│ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │Search│ │Consen│ │Reason│   │  ← Aptitude routing (HAND-BUILT rules)
│ │Agent │ │Agent │ │Agent │   │
│ └──┬───┘ └──┬───┘ └──┬───┘   │
│    │        │        │        │
│    ▼        ▼        ▼        │
│  ┌────┐  ┌────┐   ┌─────┐    │
│  │ 🐜 │  │ 🐝 │   │ LLM │    │  ← Species tools (mealpy/networkx wrappers)
│  │Ant │  │Bee │   │Human│    │
│  └──┬─┘  └──┬─┘   └──┬──┘    │
│     │       │        │        │
│     ▼       ▼        ▼        │
│  ┌──────────────────────────┐ │
│  │     Ecosystem Bus        │ │  ← HAND-BUILT (schema.py + translator.py)
│  │  BusMessage<Payload>     │ │
│  └──────────────────────────┘ │
│             │                 │
│    Synthesis (LLM)           │  ← REUSED (deepagents)
└───────────────┬───────────────┘
                │
                ▼
          Final Answer
```

## What's REUSED vs HAND-BUILT

| Component | Source |
|---|---|
| Decompose problem → subtasks | `deepagents` write_todos planner |
| Spawn subagents w/ context isolation | `deepagents` task tool |
| Route subtask → worker | `deepagents` delegation + **hand-built aptitude rules** |
| Run species algorithms | `mealpy` (ACOR, ABC, GWO, EHO, CSA) + `networkx` |
| LLM reasoning/synthesis | `langchain` chat models |
| **Typed inter-agent messages** | **HAND-BUILT: Ecosystem Bus** (`bus/schema.py`) |
| **Library output → structure** | **HAND-BUILT: Translator** (`bus/translator.py`) |

The two hand-built pieces (Ecosystem Bus + aptitude routing rules) are the
research contribution. Everything else is `pip install` + configuration.

## Quick Start

### 1. Install

```bash
cd csma
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API key:
#   OPENAI_API_KEY=sk-...
#   LLM_PROVIDER=openai
#   LLM_MODEL=gpt-4o
```

### 3. Run the Demo

```bash
python examples/delivery_planning.py
```

### 4. Run Tests

```bash
# Bus and translator tests (no API key needed)
pytest tests/test_bus_schema.py tests/test_translator.py -v

# Species tool tests (no API key needed)
pytest tests/test_ant_tool.py tests/test_bee_tool.py -v

# All tests
pytest tests/ -v
```

## Species Taxonomy

| Abstract Class | Species | Algorithm | Status |
|---|---|---|---|
| **SearchAgent** | 🐜 Ant | mealpy ACOR / networkx | ✅ Phase 1 |
| | 🫠 SlimeMold | Physarum flow (networkx) | 🔲 Phase 2 |
| **ConsensusAgent** | 🐝 Bee | mealpy ABC | ✅ Phase 1 |
| | 🐺 Wolf | mealpy GWO | 🔲 Phase 3 |
| | 🐘 Elephant | mealpy EHO | 🔲 Phase 3 |
| **ReasoningAgent** | 🧠 Human | LLM (direct) | ✅ Phase 1 |
| | 🐦‍⬛ Crow | mealpy CSA + LLM | 🔲 Phase 3 |
| **ProcessingAgent** | 🐙 Octopus | Async hub-and-arms | 🔲 Phase 3 |
| | 🐦 Starling | Boids local rules | 🔲 Phase 3 |
| | 🦗 Mantis | N parallel heads | 🔲 Phase 3 |

## Project Structure

```
csma/
├── csma/
│   ├── config.py              # LLM provider, API keys (pydantic-settings)
│   ├── runtime.py             # run_csma() — public entrypoint
│   ├── bus/
│   │   ├── schema.py          # HAND-BUILT: typed messages (BusMessage + payloads)
│   │   └── translator.py      # HAND-BUILT: raw output ↔ payload ↔ context
│   ├── species/               # Each = ONE LangChain tool wrapping a library
│   │   ├── ant.py             # mealpy ACOR → GraphPayload
│   │   ├── bee.py             # mealpy ABC → RankedOptionsPayload
│   │   ├── slime_mold.py      # (stub) networkx flow → GraphPayload
│   │   ├── wolf.py            # (stub) mealpy GWO → RankedOptionsPayload
│   │   ├── elephant.py        # (stub) mealpy EHO → RankedOptionsPayload
│   │   ├── crow.py            # (stub) mealpy CSA + LLM → TextPayload
│   │   ├── octopus.py         # (stub) async arms → FeatureStreamsPayload
│   │   ├── starling.py        # (stub) boids → FeatureStreamsPayload
│   │   └── mantis.py          # (stub) N heads → FeatureStreamsPayload
│   └── orchestrator/
│       ├── subagents.py       # 4 subagent defs with aptitude rules
│       └── deep_agent.py      # Assemble the Deep Agent (REUSE)
├── examples/
│   ├── delivery_data.json     # Problem data for the demo
│   └── delivery_planning.py   # End-to-end demo
├── tests/
│   ├── test_bus_schema.py     # Bus round-trip tests
│   ├── test_translator.py    # Translator tests
│   ├── test_ant_tool.py       # Ant tool tests
│   ├── test_bee_tool.py       # Bee tool tests
│   └── test_end_to_end.py     # Integration tests
├── pyproject.toml
├── requirements.txt
├── .env.example
└── .gitignore
```

## API Adaptations

- **mealpy 3.x**: Uses `FloatVar` for bounds, `problem_dict` format with
  `obj_func`. Classes: `OriginalACOR`, `OriginalABC`, `OriginalGWO`,
  `OriginalEHO`, `OriginalCSA` from `mealpy.swarm_based.*`.
  Result: `model.g_best.solution`, `model.g_best.target.fitness`.
- **deepagents 0.6.x**: Uses `create_deep_agent(model, system_prompt, subagents)`.
  Subagents are dicts with `name`, `description`, `system_prompt`, `tools`.
  Auto-registers `write_todos` and `task` tools.
- **CSA**: `OriginalCSA` in mealpy is **Crow Search Algorithm** (not Cuckoo
  Search, which is `OriginalCS`).
