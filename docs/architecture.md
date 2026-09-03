**English** · [Español](architecture.es.md) · [README](../README.md) · [README ES](../README.es.md)

# Architecture

For the problem statement and quickstart, see the [README](../README.md). This document is the **technical contract**: LLM boundary, tools, slice/scope, surfaces, and repo layout.

SupplyMate is a **replenishment assistant**, not a generic chat wrapper. User input enters intent routing; **Python computes qty, filters, and CSV** before any LLM narration is emitted.

## Source-of-truth layers

| Artifact | Role |
|----------|------|
| CSVs in `data/` | Primary catalog evidence |
| `app/store.py` | In-memory load + `CatalogStore` |
| `ProductMaster` | Unified row for metrics and replenishment |
| `calculate_replenishment()` | Operational qty truth |
| LLM roles | Intent, explain, insight, commit (narration only) |
| Streamlit | Consumer UI (not source of truth) |

```text
CSV → CatalogStore → ProductMaster → calculate_replenishment → REST / CSV
                                              ↑
                                    3 tools (agent path)
```

## LLM vs Python boundary

| Concern | Owner |
|---------|-------|
| `recommended_quantity` | Python (`app/replenishment.py`) |
| Slice filters, dashboard KPIs | Python (`app/services/catalog_service.py`, `dashboard.py`) |
| PO CSV rows for current scope | Python (same filters as slice) |
| Intent classification | Regex + classifier; LLM for ambiguous free text |
| SKU explanation prose | LLM, validated against Python facts |
| Explore insight / Build PO summary | LLM + `insight_validator`; deterministic fallback on failure |

**Python decides qty. LLM explains and summarizes.**

## Tool surface

Three OpenAI Agents SDK tools in [`app/tools.py`](../app/tools.py):

| Tool | Returns |
|------|---------|
| `get_inventory` | `current_stock` |
| `get_sales_history` | 30d units sold (uniform daily expansion in store) |
| `get_replenishment_params` | `lead_time_days`, `safety_stock` |

Agent flow for a single SKU: tools populate `SupplyContext` → `calculate_replenishment()` → validated explanation.

Policy constants: `HORIZON_DAYS = 7`, `HISTORY_DAYS = 30`, policy name `order-up-to`. See [`app/replenishment.py`](../app/replenishment.py).

## Slice and scope

- **`GET /replenishment/slice`** — filtered SKU rows; same predicates as purchase-list CSV.
- **`AnalyticalScope`** — category, supplier, health chips, coverage band; frozen when building a PO.
- **Clicks in Streamlit Explore** — update scope in Python; **0 LLM calls** per filter click.

[`app/services/scope.py`](../app/services/scope.py) sanitizes scope payloads. [`app/scope_builder.py`](../app/scope_builder.py) merges UI events into scope.

## Surfaces

| Surface | Port | Role |
|---------|------|------|
| FastAPI | 8000 | Runtime: `/chat`, `/replenishment/*`, `/products/*` |
| Streamlit | 8501 | Chat + Explore + Build PO + AI Analyst |
| Docker image | 8000 | API only (`COPY app`, `COPY data`; no Streamlit in image) |

Key endpoints:

- `POST /chat` — intent router + agent
- `GET /replenishment/slice` — dashboard table
- `POST /replenishment/analyze` — explore insight or commit summary
- `GET /replenishment/purchase-list.csv` — PO export for current scope

## Repo layout

| Path | Role |
|------|------|
| `app/api.py` | FastAPI app + middleware |
| `app/agent.py` | Agents: supply, explain, insight, commit |
| `app/replenishment.py` | Order-up-to formula |
| `app/tools.py` | 3 inventory tools |
| `app/services/` | catalog, dashboard, metrics, scope, insight validator |
| `app/middleware/` | rate limit, safe errors, security headers |
| `ui/` | Streamlit app |
| `data/` | Resource CSVs (see [data-contract.md](data-contract.md)) |
| `tests/` | pytest + golden CSVs |
| `openspec/` | Internal SDD (strict TDD specs per change) |

Internal specs live under `openspec/changes/` — not the public README index.
