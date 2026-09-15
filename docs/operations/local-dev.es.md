**Español** · [English](local-dev.md) · [README ES](../../README.es.md)

# Desarrollo local

Runbook para desarrolladores: fórmula, smoke de API, Docker y la tabla extendida “¿por qué no X?”. Para la landing de portfolio, ver el [README ES](../../README.es.md).

*Términos técnicos en inglés a propósito: slice, SKU, ROP, tools, qty, insight.*

## Stack

| Superficie | Default | Notas |
|------------|---------|--------|
| FastAPI | `127.0.0.1:8000` | Si está ocupado, usá `8001` y apuntá Vite ahí |
| UI Vite | `127.0.0.1:8080` | `VITE_SUPPLYMATE_API_URL` en `frontend/.env` |
| Docker | Solo API en `8000` | No incluye la UI Vite |

## Política de reposición (honesta)

**Order-up-to / periodic review**

```text
avg_daily      = total_units_sold_last_30 / 30
demand_horizon = avg_daily * 7
demand_lead    = avg_daily * lead_time_days
stock_target   = demand_horizon + demand_lead + safety_stock
recommended    = max(0, ceil(stock_target - current_stock))
```

- **Punto de reorden** es una alarma de salud (“Riesgo de quiebre”). No entra en la cantidad a pedir.
- **Cobertura** = stock / demanda diaria 30d. Aproximación, no un forecast.
- **Riesgo de quiebre** = regla (`qty > 0` y stock ≤ ROP). No es una probabilidad.
- **Sobrestock** = stock > máximo y qty = 0. No es dead stock.
- Las ventas diarias del historial se **expanden de forma uniforme** a partir del total 30d. No hay serie temporal real: no infieras tendencia ni estacionalidad.

No es un modelo de demanda ML. Detalle: [`docs/contract/architecture.es.md`](../contract/architecture.es.md).

## Camino feliz (recordatorio)

```bash
pip install -e ".[dev]"
cp .env.example .env   # GROQ_API_KEY (o DeepSeek / OpenAI-compatible)
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

## Smoke de API

Con uvicorn en `:8000`:

```powershell
.\scripts\smoke_api.ps1
```

Curls manuales:

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
  -d "{\"message\": \"¿Cuánto debería pedir de 6033436?\"}"

curl -s -X POST http://127.0.0.1:8000/replenishment/analyze \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"explore\",\"scope\":{},\"events\":[],\"root_question\":\"¿Qué comprar?\"}"
```

## Docker (solo API)

```bash
docker build -t supplymate .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=gsk-... -e LLM_PROVIDER=groq supplymate
```

## ¿Por qué no usar X? (extendida)

| Alternativa | Por qué no en este MVP |
|-------------|-------------------------|
| **RAG / embeddings / vector DB** | CSV estructurado; matching lexical de SKU. Sin embeddings en runtime. |
| **LangChain / LangGraph** | Overkill para 3 tools de inventario; OpenAI Agents SDK |
| **Que el LLM calcule** | Los números críticos no se alucinan; Python calcula y valida la narración |
| **Multi-agent swarm** | Roles LLM separados (intent / explain / insight / commit), no un enjambre |
| **Forecasting / ML / EOQ** | Fuera de scope; la política es explícita y simple |
| **Postgres / dbt / Airflow / Superset** | Overkill; el dashboard vive en la UI de chat |
| **Que el LLM filtre 13k filas** | Filtros y KPIs son Python sobre el scope activo; el modelo no es dueño del panel |

Versión corta para lectores de portfolio: [README ES → ¿Por qué no usar X?](../../README.es.md#por-qué-no-usar-x).

## Relacionado

- [`frontend/README.md`](../../frontend/README.md) — env Vite y dueño del panel
- [`docs/operations/recorte-coherence.md`](recorte-coherence.md) — dueño del panel + invariantes
- [`docs/contract/evaluation.es.md`](../contract/evaluation.es.md) — markers pytest y CI
