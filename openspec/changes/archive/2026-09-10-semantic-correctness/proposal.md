# Proposal: semantic-correctness

## Why

The product already has drill-down, slice, and validated LLM insights. The remaining gaps are honesty and AI-engineering: dead embedding deps that contradict the README, an unnamed replenishment policy vs `reorder_point`, no evals for the generative path, and purchase lines without value or operational priority.

## What Changes

- Remove unused semantic product resolution and heavy deps (`sentence-transformers`, `numpy`)
- Name the order-up-to policy; treat `reorder_point` as a health alarm only
- Metric contracts (coverage, stockout risk, overstock) with explicit caveats
- `math.ceil` on recommended quantity
- Golden intents CSV + `@pytest.mark.llm` (excluded from CI)
- Insight/explain orphan-number evals; deterministic fallback for SKU narration
- JSON stdout log per `Runner.run`
- README product-first demo
- `operational_priority` + `estimated_purchase_value` (qty × `price`, never PVP)

## Non-Goals

- RAG, live embeddings, vector DB
- Forecasting, EOQ, ABC/XYZ, service levels
- OpenTelemetry / LangSmith / Groq structured outputs
- Splitting `catalog_service.py`
- GIF / React / DuckDB / MCP
