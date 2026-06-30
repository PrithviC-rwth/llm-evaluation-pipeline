# Phase 2: Agent Harness with Human Checkpoints

## Goal

Wrap the Phase 1 pipeline tools in a LangGraph-powered AI Agent that runs each data engineering stage autonomously, identifies issues, attempts fixes, and pauses for human approval at critical decision points.

The Agent must behave like a Digital Data Engineer: it reasons about what it finds, proposes actions, and escalates the right issues to a human before proceeding.

---

## Prerequisites

- Phase 1 complete and all tests passing.
- Add to `pyproject.toml` dependencies:
  - `langgraph>=0.2`
  - `langchain-core>=0.2`
  - `langchain-openai>=0.1` (or the relevant provider)

Run `uv sync` after updating dependencies.

---

## Concepts

### Agent State

A shared `TypedDict` object passed between every node in the graph. Every node reads from it and writes updates to it. Nothing is stored outside of state.

### Nodes

Each pipeline stage (ingest, transform, validate, fix, store, report) becomes a LangGraph node. A node is a Python function that receives state and returns a partial state update.

### Edges and Conditional Routing

After validation, a conditional edge routes to:

- `auto_fix` node — if issues are minor and auto-fixable
- `human_checkpoint` node — if issues are critical or ambiguous
- `store` node — if no issues found

### Interrupt (Human Checkpoint)

LangGraph's `interrupt()` function pauses graph execution and surfaces a message to the human. Execution resumes only after the human provides a decision. The decision is stored in state and used by the next node.

---

## Checkpoint Tiers

| Tier | Trigger condition | Human action required |
|---|---|---|
| Auto-fix | Null rate < 5%, type coercion, whitespace | None — agent proceeds automatically |
| Review | Null rate 5–10%, unexpected column added, row count deviation > 5% | Human confirms proposed fix |
| Approval | Null rate > 10%, writing to production storage, dropping > 5% of rows | Human chooses fix strategy |
| Hard stop | Schema mismatch, critical check fails with no safe fix | Human must provide explicit instruction |

---

## File Structure to Create

```text
llm_eval_pipeline/
├── agent/
│   ├── __init__.py
│   ├── state.py           # TypedDict for shared agent state
│   ├── tools.py           # Pipeline stages wrapped as agent-callable tools
│   ├── nodes.py           # LangGraph node functions
│   ├── checkpoints.py     # Checkpoint condition logic and interrupt messages
│   └── graph.py           # Builds and compiles the LangGraph StateGraph
└── tests/
    └── test_agent_graph.py
```

---

## Tasks

### T2.1 — `agent/state.py`

Define `PipelineState` as a `TypedDict` with these fields:

- `raw_df` — raw ingested DataFrame (or None)
- `transformed_df` — cleaned DataFrame (or None)
- `aggregated_df` — aggregated DataFrame (or None)
- `issues` — list of issue dicts from validator (default empty list)
- `fix_history` — list of strings describing each fix applied
- `human_decisions` — dict mapping checkpoint name to human response string
- `report_path` — path of the written quality report (or None)
- `status` — one of `RUNNING`, `AWAITING_HUMAN`, `COMPLETED`, `FAILED`

### T2.2 — `agent/tools.py`

Wrap each Phase 1 pipeline function as a tool the agent nodes can call:

- `run_ingest(state) -> dict` — calls `ingestor.ingest()`, updates `raw_df`
- `run_transform(state) -> dict` — calls `transformer.transform()`, updates `transformed_df`
- `run_aggregate(state) -> dict` — calls `aggregator.aggregate()`, updates `aggregated_df`
- `run_validate(state) -> dict` — calls `validator.validate()`, updates `issues`
- `run_report(state) -> dict` — calls `reporter.generate_report()`, updates `report_path`

Each tool must catch exceptions and add a `CRITICAL` issue to `state["issues"]` rather than raising.

### T2.3 — `agent/checkpoints.py`

Define two functions:

- `classify_issues(issues: list[dict]) -> str`
  - Returns `"auto_fix"`, `"review"`, `"approval"`, or `"hard_stop"` based on checkpoint tier table above

- `build_checkpoint_message(issues: list[dict], state: PipelineState) -> str`
  - Returns a human-readable summary of what was found and what the agent proposes to do
  - Format: what was found / proposed action / what happens if approved / what happens if rejected

### T2.4 — `agent/nodes.py`

Implement the following node functions:

- `ingest_node(state)` — calls `run_ingest`, returns updated state
- `transform_node(state)` — calls `run_transform`, returns updated state
- `aggregate_node(state)` — calls `run_aggregate`, returns updated state
- `validate_node(state)` — calls `run_validate`, returns updated state
- `auto_fix_node(state)` — applies safe fixes (drop exact duplicates, fill nulls with median for numeric columns), appends to `fix_history`
- `human_checkpoint_node(state)` — calls `interrupt()` with the checkpoint message; on resume, reads human decision from state and routes accordingly
- `store_node(state)` — writes `aggregated_df` to Parquet at `config.OUTPUT_PATH`
- `report_node(state)` — calls `run_report`, sets `status = COMPLETED`

### T2.5 — `agent/graph.py`

Build the `StateGraph`:

1. Add all nodes from T2.4
2. Set `ingest_node` as entry point
3. Add sequential edges: `ingest → transform → aggregate → validate`
4. Add conditional edge from `validate_node` using `classify_issues` result:
   - `"auto_fix"` → `auto_fix_node` → back to `validate_node`
   - `"review"` or `"approval"` → `human_checkpoint_node`
   - `"hard_stop"` → `human_checkpoint_node`
   - No issues → `store_node`
5. Add edge: `human_checkpoint_node → store_node` (after approval)
6. Add edge: `store_node → report_node`
7. Compile graph with a `MemorySaver` checkpointer so state persists across interrupts

Export a `run_agent(dry_run: bool = False) -> PipelineState` function that invokes the graph with an initial empty state.

### T2.6 — `run_agent.py` (CLI entry point)

- Calls `run_agent()` and loops until `state["status"]` is `COMPLETED` or `FAILED`
- When `status == AWAITING_HUMAN`, prints the checkpoint message and reads input from stdin
- Passes the human response back to the graph via `graph.update_state()`
- Accepts `--dry-run` flag (passes through to agent)
- Prints final summary: stages completed, fixes applied, report path

### T2.7 — Unit Tests (`tests/test_agent_graph.py`)

- Test that `classify_issues` returns the correct tier for each scenario
- Test that `auto_fix_node` removes duplicates from a fixture DataFrame
- Test that the full graph runs end-to-end on clean data without triggering a checkpoint
- Test that the graph pauses (raises `GraphInterrupt`) when a critical issue is injected

---

## Acceptance Criteria

- `uv run python run_agent.py` runs the full pipeline with human interaction via stdin
- `uv run python run_agent.py --dry-run` prints stages and checkpoint messages without writing to disk
- The graph pauses when a critical issue is present and resumes correctly after human input
- `uv run pytest tests/test_agent_graph.py` passes with no failures
- `fix_history` in final state accurately records every change the agent made
