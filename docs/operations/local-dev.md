**English** · [Español](local-dev.es.md) · [README](../../README.md)

# Local development

Runbook for developers: formula details, API smoke, Docker, and the extended “why not X” table. For the portfolio landing, see the [README](../../README.md).

## Stack

| Surface | Default | Notes |
|---------|---------|--------|
| FastAPI | `127.0.0.1:8000` | If busy, use `8001` and point Vite at it |
| Vite UI | `127.0.0.1:8080` | `VITE_SUPPLYMATE_API_URL` in `frontend/.env` |
| Docker | API only on `8000` | Does not ship the Vite UI |

## Replenishment policy (honest)

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

This is not an ML demand model. Details: [`docs/contract/architecture.md`](../contract/architecture.md).

## Happy path (reminder)

```bash
pip install -e ".[dev]"
cp .env.example .env   # set GROQ_API_KEY (or DeepSeek / OpenAI-compatible)
pytest -m "not performance and not llm"
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
cp .env.example .env   # VITE_SUPPLYMATE_API_URL=http://127.0.0.1:8000
npm install
npm run dev -- --host 127.0.0.1 --port 8080
```

## API smoke

With uvicorn on `:8000`:

```powershell
.\scripts\smoke_api.ps1
```

Manual curls:

```bash
curl -s http://127.0.0.1:8000/health
curl -s "http://127.0.0.1:8000/products/search?q=47%20street"
curl -s http://127.0.0.1:8000/products/6033436/replenishment
# → recommended_quantity: 173

curl -s "http://127.0.0.1:8000/replenishment/slice?limit=5"
curl -s "http://127.0.0.1:8000/replenishment/slice?category=Cabello&limit=5"
curl -s "http://127.0.0.1:8000/replenishment/purchase-list.csv?limit=10" -o purchase_order.csv

curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"How much should I order of 6033436?\"}"

curl -s -X POST http://127.0.0.1:8000/replenishment/analyze \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"explore\",\"scope\":{},\"events\":[],\"root_question\":\"What to buy?\"}"
```

## Docker (API only)

```bash
docker build -t supplymate .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=gsk-... -e LLM_PROVIDER=groq supplymate
```

## Why not just use X? (extended)

| Alternative | Why not in this MVP |
|-------------|---------------------|
| **RAG / embeddings / vector DB** | Structured CSV; lexical SKU matching. No embedding models at runtime. |
| **LangChain / LangGraph** | Overkill for 3 inventory tools; OpenAI Agents SDK |
| **Let the LLM calculate** | Critical numbers are not hallucinated; Python calculates and validates narration |
| **Multi-agent swarm** | Separate LLM roles (intent / explain / insight / commit), not a swarm |
| **Forecasting / ML / EOQ** | Out of scope; policy is explicit and simple |
| **Postgres / dbt / Airflow / Superset** | Overkill; dashboard lives in the chat UI |
| **LLM filters 13k rows** | Filters and KPIs are Python on the active scope; the model does not own the panel |

Short version for portfolio readers: [README → Why not just use X?](../../README.md#why-not-just-use-x).

## Related

- [`frontend/README.md`](../../frontend/README.md) — Vite env and panel owner notes
- [`docs/operations/recorte-coherence.md`](recorte-coherence.md) — panel owner + coherence invariants
- [`docs/contract/evaluation.md`](../contract/evaluation.md) — pytest markers and CI
