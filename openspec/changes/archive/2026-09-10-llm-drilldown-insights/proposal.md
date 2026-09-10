# Proposal: llm-drilldown-insights

## Why

Operators need Ask-style exploration (understand inventory via clicks + LLM) before Agent-style commit (freeze scope, export OC). Deterministic slice alone is silent; LLM adds interpretation without inventing quantities.

## What Changes

- `POST /replenishment/analyze` with `mode=explore|commit`
- `InteractionEvent` log + `PromptCompiler`
- `DashboardInsight` (explore) + `CommitSummary` (commit)
- Streamlit modes: **Explorar** / **Armar OC** with `frozen_scope`
- Export CSV only in commit mode

## Non-Goals

- LLM does not filter rows or choose chips
- LLM does not modify qty or CSV bytes
- No changes to `intents.py`
