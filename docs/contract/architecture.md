**English** · [Español](architecture.es.md) · [README](../README.md) · [README ES](../README.es.md)

# Architecture

For the problem statement and quickstart, see the [README](../README.md). This document is the **technical contract**: LLM boundary, tools, slice/scope, surfaces, and repo layout.

SupplyMate is a **replenishment assistant**, not a generic chat wrapper. User input enters intent routing; **Python computes qty, filters, and CSV** before any LLM narration is emitted.

## Source-of-truth layers

| Artifact | Role |
|----------|------|
| CSVs in `data/` | Primary catalog evidence |
| `app/catalog/store.py` | In-memory load + `CatalogStore` |
| `ProductMaster` | Unified row for metrics and replenishment |
| `calculate_replenishment()` | Operational qty truth |
| LLM roles | Intent, explain, insight, optional commit narration |
| Vite frontend | Live consumer UI (not source of truth) |

```text
CSV → CatalogStore → ProductMaster → calculate_replenishment → REST / CSV
                                              ↑
                                    3 tools (agent path)
```

## LLM vs Python boundary

| Concern | Owner |
|---------|-------|
| `recommended_quantity` | Python (`app/core/replenishment.py`) |
| Slice filters, dashboard KPIs | Python (`app/services/analytics/catalog_service.py`, `dashboard.py`) |
| PO CSV rows for current scope | Python (same filters as slice) |
| Intent classification | Regex + classifier; LLM for ambiguous free text |
| SKU explanation prose | LLM, validated against Python facts |
| Explore insight / optional PO summary | LLM + `insight_validator`; deterministic fallback on failure |

**Python decides qty. LLM explains and summarizes.**

## Tool surface

Three OpenAI Agents SDK tools in [`app/agent/tools.py`](../app/agent/tools.py):

| Tool | Returns |
|------|---------|
| `get_inventory` | `current_stock` |
| `get_sales_history` | 30d units sold (uniform daily expansion in store) |
| `get_replenishment_params` | `lead_time_days`, `safety_stock` |

Agent flow for a single SKU: tools populate `SupplyContext` → `calculate_replenishment()` → validated explanation.

Policy constants: `HORIZON_DAYS = 7`, `HISTORY_DAYS = 30`, policy name `order-up-to`. See [`app/core/replenishment.py`](../app/core/replenishment.py).

## Slice and scope

- **`GET /replenishment/slice`** — filtered SKU rows and dashboard for the active `UiSlice`; **single owner of Explore KPIs / chart / table**.
- **`AnalyticalScope`** — category, subcategory, supplier, health, coverage, name tokens, horizon.
- **Chat board** — optimistic placeholder only while the slice query is loading; never durable truth over a changed scope.
- **Clicks in the Explore panel** — update scope via slice query params; **0 LLM calls** per filter click.
- **Filter algebra** (`filter_rows`): same axis → OR; distinct axes → AND.
- **Operator-driven cart** — Explore suggests; the operator adds lines, edits `order_quantity` in Review PO, and picks CSV columns on export.

[`app/services/scoping/scope_sanitize.py`](../../app/services/scoping/scope_sanitize.py) sanitizes scope payloads. [`app/pipeline/scope_builder.py`](../../app/pipeline/scope_builder.py) merges UI events into scope. Coherence checklist: [`docs/operations/recorte-coherence.md`](../operations/recorte-coherence.md).

## Surfaces

| Surface | Port | Role |
|---------|------|------|
| FastAPI | 8000 | Runtime: `/chat`, `/replenishment/*`, `/products/*` |
| Vite frontend (`frontend/`) | 8080 | Live UI: chat + Explore + Review PO |
| Docker image | 8000 | API only (`COPY app`, `COPY data`) |

Key endpoints:

- `POST /chat` — intent router + agent
- `GET /replenishment/slice` — dashboard + table for active scope
- `POST /replenishment/analyze` — explore insight or commit summary
- `GET /replenishment/purchase-list.csv` — server-side PO export for a scope
- Client cart CSV — operator column picker in Review PO (default barcode + qty)
## Repo layout

Layered layout — detail in [`app/README.md`](../../app/README.md) and [`tests/README.md`](../../tests/README.md). Index: [`docs/README.md`](../README.md).

| Path | Role |
|------|------|
| `app/api.py` | FastAPI app + middleware |
| `app/core/` | Models, config, replenishment formula |
| `app/catalog/` | CSV store, product resolution |
| `app/pipeline/` | Query interpretation → reference resolution → scope |
| `app/guidance/` | Chips, missions, guided next question |
| `app/agent/` | LLM agents, tools, intent routing (`runner.py`) |
| `app/services/analytics/` | Slice, dashboard, metrics |
| `app/services/scoping/` | Scope mutations, panel modes, suggested filters |
| `app/services/insight/` | Prompt compiler, validator, insight cache |
| `app/middleware/` | Rate limit, safe errors, security headers |
| `frontend/` | Live Vite UI (Explore / Review PO) |
| `data/` | Resource CSVs (see [data-contract.md](data-contract.md)) |
| `tests/` | Layered pytest + golden CSVs |
| `docs/contract/` | Public architecture, evaluation, data contract |
| `docs/operations/` | Maintenance, security, performance |
| `openspec/` | Internal SDD (strict TDD specs per change) |

Internal specs live under `openspec/changes/` — not the public README index.
