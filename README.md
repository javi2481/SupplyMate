# SupplyMate

*English* · [Español](README.es.md)

AI Engineering MVP for replenishment in distribution SMBs.

**Principle:** *LLM orchestrates, deterministic code decides.*

## Why it exists

A distribution SMB needs to answer:

> How much of product X should I order to cover the next 7 days?

If the LLM invents stock, sales, or quantity, the system is not trustworthy. SupplyMate separates roles:

- the **LLM orchestrates** (intent, explanation, insight)
- **Python code decides** (formula, filters, CSV)

## Who this is for

- **Applied AI engineers** who want a *tool-calling + deterministic logic + validated insights* case study
- **Operations / supply** teams who need an exportable purchase order on the same slice they see
- **Interviews** — small, testable, easy-to-narrate MVP

## Why not just use X?

| Alternative | Why not in this MVP |
|-------------|---------------------|
| **RAG / embeddings / vector DB** | Structured CSV; lexical SKU matching. No embedding models at runtime. |
| **LangChain / LangGraph** | Overkill for 3 inventory tools; OpenAI Agents SDK |
| **Let the LLM calculate** | Critical numbers are not hallucinated; Python calculates and validates narration |
| **Multi-agent swarm** | Separate LLM roles (intent / explain / insight / commit), not a swarm |
| **Forecasting / ML / EOQ** | Out of scope; policy is explicit and simple |
| **Postgres / dbt / Airflow / Superset** | Overkill; dashboard lives in chat |

## How it works

```text
User
  ↓
/chat  ── regex or intent classifier
  ├── list / dashboard  → Python slice (0 LLM per click)
  └── single SKU        → 3 tools → calculate_replenishment → explanation (validated)
/replenishment/slice     → same filters as CSV export
/replenishment/analyze   → insight or PO summary, validator, deterministic fallback
```

| Piece | Role |
|-------|------|
| CSVs in [`data/`](data/) | Simulated catalog (~13k SKUs) |
| [`app/services/analytics/metrics.py`](app/services/analytics/metrics.py) | Metric contracts + coverage + health + priority |
| 3 tools + [`app/core/replenishment.py`](app/core/replenishment.py) | Inventory / sales / params; qty in Python |
| LLM roles | Intent, SKU explainer, insight (Explore); commit summary optional |
| REST | search, replenishment, `/chat`, `/slice`, `/analyze`, dashboard, CSV |
| Vite frontend (`frontend/`) | Live UI: chat + **Explore** / **Review PO** |

### Replenishment policy (honest)

**Order-up-to / periodic review**

```text
avg_daily      = total_units_sold_last_30 / 30
demand_horizon = avg_daily * 7
demand_lead    = avg_daily * lead_time_days
stock_target   = demand_horizon + demand_lead + safety_stock
recommended    = max(0, ceil(stock_target - current_stock))
```

- **Reorder point** is a health alarm (“stockout risk”). It does not enter the order quantity.
- **Coverage** = stock / 30d daily demand. Approximation, not a forecast.
- **Stockout risk** = rule (`qty > 0` and stock ≤ ROP). Not a probability.
- **Overstock** = stock > max and qty = 0. Not dead stock.
- Daily sales in history are **expanded uniformly** from the 30d total. No real time series: do not infer trend or seasonality.

This is not an ML demand model. The MVP demonstrates deterministic replenishment + conversational analytics.

Details: [`docs/contract/architecture.md`](docs/contract/architecture.md)

## What the MVP proves

**Real catalog** — `6033436` → qty **173**; `8141600` → **0**. Operator-driven cart → Review PO → CSV with a **column picker** (default `barcode` + `order_quantity`; optional product id/name, category, supplier, suggested qty, estimated value). Purchase value = qty × list price (not retail PVP).

Panel truth: KPIs / chart / table come from `GET /replenishment/slice` for the active scope (see [`docs/operations/recorte-coherence.md`](docs/operations/recorte-coherence.md)).

### Screenshots

![Explore panel — chat + KPIs + chart](docs/assets/explore-panel.png)

![Review PO — export column picker](docs/assets/oc-export-columns.png)

## What the clone includes

| Ready to clone | Optional |
|----------------|----------|
| CSVs in [`data/`](data/) | `GROQ_API_KEY` in `.env` (or DeepSeek / OpenAI) |
| pytest tests | Paid OpenAI |
| FastAPI + agent + formula | |
| Vite frontend (`frontend/`) | |

## Quickstart

```bash
git clone https://github.com/javi2481/SupplyMate.git
cd SupplyMate
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env and set GROQ_API_KEY (https://console.groq.com/keys)

pytest -m "not performance and not llm"
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
cp .env.example .env   # VITE_SUPPLYMATE_API_URL=http://127.0.0.1:8000
npm install
npm run dev -- --host 127.0.0.1 --port 8080
```

Open **http://127.0.0.1:8080**. If port `8000` is already taken on your machine, run the API on `8001` and set `VITE_SUPPLYMATE_API_URL` accordingly.

API smoke (with uvicorn on :8000):

```powershell
.\scripts\smoke_api.ps1
```

### The flow (under 2 minutes)

1. Ask: **What products should I buy?**
2. Click a **health chip** or a **chart bar** → refine the slice (KPIs/table follow `/slice`)
3. **Add to order** on the SKUs you want (chat suggests; the operator decides)
4. Open **Review PO** → adjust quantities → **Export and finish** → pick CSV columns (barcode + qty by default)

Clicks, filters, and CSV = **0 LLM calls**. The model runs on free-form questions and SKU explanation.

Demo SKU: `6033436`. Vocabulary: Stockout risk, Out of stock, Overstock, Coverage, Recommended quantity.

Examples:

- `How much should I order of 6033436?` → qty + **How it was calculated**
- `What products should I buy?` → **Explore** → add lines → **Review PO** → **Export CSV**

```bash
curl -s -X POST http://127.0.0.1:8000/replenishment/analyze \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"explore\",\"scope\":{},\"events\":[],\"root_question\":\"What to buy?\"}"
```

First verifiable result:

```bash
curl -s http://127.0.0.1:8000/products/6033436/replenishment
# → recommended_quantity: 173
```

## Terminal flow

**SKU path**

```text
Question: How much should I order of 6033436?
   ↓
Intent → 3 tools → calculate_replenishment
   ↓
Answer: qty 173 + How it was calculated (validated)
```

**Slice + cart path**

```text
Question: What products should I buy?
   ↓
Explore panel → clicks (0 LLM) → Add to order → Review PO → CSV columns
   ↓
If LLM insight fails → deterministic fallback
```

```bash
curl -s http://127.0.0.1:8000/health
curl -s "http://127.0.0.1:8000/products/search?q=47%20street"
curl -s http://127.0.0.1:8000/products/6033436/replenishment
curl -s "http://127.0.0.1:8000/replenishment/slice?limit=5"
curl -s "http://127.0.0.1:8000/replenishment/slice?category=Cabello&limit=5"
curl -s "http://127.0.0.1:8000/replenishment/purchase-list.csv?limit=10" -o purchase_order.csv
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"How much should I order of 6033436?\"}"
```

## Scope

| Included | Excluded |
|----------|----------|
| 3 inventory tools + bounded LLM roles | RAG, embeddings, vector DB |
| Deterministic order-up-to calculation | Forecasting / ML / EOQ |
| CSV catalog | Postgres app DB / dbt / Airflow / Superset |
| Vite Explore / Review PO UI | Mandatory separate BI tool |
| Operator-driven cart + column-picker CSV | Multi-agent swarm / LangChain |
| `/replenishment/analyze` (LLM interprets, Python calculates; optional insight API) | LLM calculates qty or filters rows |
| Insight evals + golden intents (CI without live LLM) | LangSmith / OpenTelemetry |

## Live UI

Chat + **Explore** / **Review PO** at http://127.0.0.1:8080 against the API on `:8000`. See [`frontend/README.md`](frontend/README.md).

UI scaffold originated in Lovable; the product surface is this Vite app under `frontend/`.

Docker (API only):

```bash
docker build -t supplymate .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=gsk-... -e LLM_PROVIDER=groq supplymate
```

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/README.md`](docs/README.md) | Doc index (contract / operations / templates) |
| [`app/README.md`](app/README.md) | Application code layers |
| [`tests/README.md`](tests/README.md) | Test suite layers |
| [`docs/contract/architecture.md`](docs/contract/architecture.md) | LLM vs Python boundary, tools, slice/scope, layout |
| [`docs/contract/evaluation.md`](docs/contract/evaluation.md) | CI, goldens, pytest markers, performance |
| [`docs/contract/data-contract.md`](docs/contract/data-contract.md) | CSV contract / `product_id` |

Internal SDD: [`openspec/`](openspec/) (per-change specs; not the public entry point).

### Quality and maintenance

| Doc | Contents |
|-----|-----------|
| [`docs/operations/recorte-coherence.md`](docs/operations/recorte-coherence.md) | Panel owner + six coherence invariants |
| [`docs/operations/maintenance-policy.md`](docs/operations/maintenance-policy.md) | Lehman laws, preventive sprint |
| [`docs/operations/beta-test-protocol.md`](docs/operations/beta-test-protocol.md) | Beta scenario + UX checklist |
| [`docs/operations/security-audit-osstmm-lite.md`](docs/operations/security-audit-osstmm-lite.md) | Lite web audit |
| [`docs/operations/compatibility-matrix.md`](docs/operations/compatibility-matrix.md) | Browsers / OS |
| [`docs/operations/performance-profile.md`](docs/operations/performance-profile.md) | Performance smoke thresholds |
| [`openspec/changes/archive/2026-09-10-engineering-quality/traceability-matrix.md`](openspec/changes/archive/2026-09-10-engineering-quality/traceability-matrix.md) | MUST → test (archived) |

**Status:** v0.5.0 — conversational replenishment + sliceable Explore panel; qty and filters in Python; operator-driven PO cart; LLM on free-form question / insight only.

### Design decisions (interview-ready)

1. **Numbers never come from the model** — `calculate_replenishment()` owns qty; the LLM narrates validated facts.
2. **One panel owner** — `/replenishment/slice` for the active `UiSlice`; chat board is only a loading placeholder.
3. **Operator owns the PO** — chat suggests; the human adds lines, edits qty, and chooses CSV columns.

### Next milestones

1. **Second catalog source** — validate the CSV contract with another dataset
2. **API auth** — endpoints ready for controlled deployment
3. **Query interpretation** — harden multiturn goldens and reference resolution
4. **Richer PO formats** — ERP templates beyond the column picker (EDI, XLSX, etc.)

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Repository health

[![CI](https://github.com/javi2481/SupplyMate/actions/workflows/ci.yml/badge.svg)](https://github.com/javi2481/SupplyMate/actions/workflows/ci.yml)

CI runs `pytest -m "not performance and not llm"`, coverage ≥85% on critical modules, and Docker smoke. Marker `llm` excluded from main CI.

```bash
pytest -m "not performance and not llm"
pytest -m performance   # performance smoke (main CI only)
# Live LLM paraphrase evals (not CI): RUN_LLM_EVALS=1 pytest -m llm
```

## License

MIT — see [`LICENSE`](LICENSE).
