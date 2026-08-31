# SupplyMate

MVP de AI Engineering para reabastecimiento en pymes de distribución.

**Principio:** *LLM orchestrates, deterministic code decides.*

Un chat: preguntás **cuánto pedir** o **qué está pasando**, y el dashboard (KPIs + gráficos + OC) sale en la respuesta. Tras *¿Qué productos tengo que comprar?* podés **recortar** el panel con clicks (categoría, cobertura, chips) y exportar **esa** OC — sin volver a preguntar al LLM.

Vocabulario: Riesgo de quiebre, Falta de stock, Sobrestock, Cobertura, Cantidad recomendada. SKU demo: `6033436`.

## Por qué existe

Una pyme de distribución necesita responder:

> ¿Cuánto debería pedir del producto X para cubrir los próximos 7 días?

Si el LLM inventa el stock, las ventas o la cantidad a pedir, el sistema no es confiable. SupplyMate separa roles:

- el **LLM orquesta** (elige tools y explica)
- el **código Python decide** (fórmula determinística de reabastecimiento)

El dashboard del chat lee **las mismas** cantidades; no hay BI aparte ni fórmula en SQL.

## Para quién es

- **AI / ML engineers** que quieren un caso claro de *tool-calling + lógica determinística*
- **Equipos de operaciones / supply** que necesitan una recomendación concreta + OC exportable
- **Candidatos a entrevistas** que buscan un MVP chico, testeable y fácil de narrar

## ¿Por qué no usar X?

| Alternativa | Por qué no en este MVP |
|-------------|-------------------------|
| **RAG / embeddings / vector DB** | Los datos ya son CSV estructurados; no hay documentos que recuperar |
| **LangChain / LangGraph** | Overkill para 1 agente + 3 tools; usamos OpenAI Agents SDK |
| **Que el LLM calcule** | Los números críticos no deben alucinarse; Python calcula |
| **Multi-agent / handoffs** | Un solo agente alcanza para esta pregunta |
| **Forecasting / ML / EOQ** | Fuera de scope; la fórmula es explícita y simple |
| **Postgres / dbt / Airflow / Superset** | Overkill; el dashboard vive en el chat |

## Cómo funciona SupplyMate

```text
User (chat)
  ↓
Agent (OpenAI Agents SDK + Groq free tier)
  ↓
Tools
  ├── get_inventory
  ├── get_sales_history
  └── get_replenishment_params
  ↓
Deterministic calculation (Python)
  ↓
Recommendation (recommended_quantity)
  ↓
Explanation (LLM, solo narra los números)
```

| Pieza | Rol |
|-------|-----|
| CSVs en [`data/`](data/) | **API simulada** (~13k SKUs) |
| [`app/services/metrics.py`](app/services/metrics.py) | Labels + Coverage + health buckets |
| 3 tools + [`app/replenishment.py`](app/replenishment.py) | Fórmula 7 días |
| REST | search, replenishment, `/chat`, `/replenishment/slice`, `/replenishment/analyze`, dashboard, `purchase-list.csv` |
| Streamlit | Chat + panel **Explorar (Ask)** / **Armar OC (Agent)** + Analista IA |

**Fórmula:**

```text
avg_daily      = total_units_sold_last_30 / 30
demand_horizon = avg_daily * 7
demand_lead    = avg_daily * lead_time_days
stock_target   = demand_horizon + demand_lead + safety_stock
recommended    = max(0, stock_target - current_stock)
```

SDD: [`openspec/changes/mvp-core/`](openspec/changes/mvp-core/) + [`openspec/changes/dual-surface-analytics/`](openspec/changes/dual-surface-analytics/) + [`openspec/changes/interactive-drilldown/`](openspec/changes/interactive-drilldown/) + [`openspec/changes/llm-drilldown-insights/`](openspec/changes/llm-drilldown-insights/).

## Qué demuestra el MVP

**Catálogo real** — `6033436` → cantidad recomendada **172**; `8141600` → **0**.

Lista de compras + CSV OC (`barcode,product_id,product_name,supplier,recommended_quantity`).

## Qué trae el clone

| Listo al clonar | Opcional |
|-----------------|----------|
| CSVs en [`data/`](data/) | `GROQ_API_KEY` en `.env` |
| Tests pytest | Streamlit |
| FastAPI + agente + fórmula | Streamlit (chat + dashboard) |
| SDD en [`openspec/`](openspec/) | OpenAI pago |

## Inicio rápido

```bash
git clone <este-repo>
cd SupplyMate
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Editar .env y poner GROQ_API_KEY (https://console.groq.com/keys)

pytest
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

En otra terminal:

```bash
streamlit run ui/streamlit_app.py
```

Abrí http://localhost:8501.

Smoke de API (con uvicorn en :8000):

```powershell
.\scripts\smoke_api.ps1
```

Ejemplos:

- `¿Cuánto debería pedir de 6033436?` → qty + **Cómo se calculó**
- `¿Qué productos tengo que comprar?` → panel **Explorar** (clicks + Analista IA) → **Listo — armar OC** → **Exportar OC** en modo Agent

```bash
curl -s -X POST http://127.0.0.1:8000/replenishment/analyze \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"explore\",\"scope\":{},\"events\":[],\"root_question\":\"¿Qué comprar?\"}"
```

## Flujo en terminal

```bash
curl -s http://127.0.0.1:8000/health
curl -s "http://127.0.0.1:8000/products/search?q=47%20street"
curl -s http://127.0.0.1:8000/products/6033436/replenishment
curl -s "http://127.0.0.1:8000/replenishment/slice?limit=5"
curl -s "http://127.0.0.1:8000/replenishment/slice?category=Cabello&limit=5"
curl -s "http://127.0.0.1:8000/replenishment/purchase-list.csv?limit=10" -o purchase_order.csv
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"¿Cuánto debería pedir de 6033436?\"}"
```

## Alcance

| Incluido | Excluido |
|----------|----------|
| 1 agente + 3 tools | RAG, embeddings, vector DB |
| Cálculo determinístico | Forecasting / ML / EOQ |
| Catálogo CSV | Postgres app DB / dbt / Airflow / Superset |
| Streamlit Explorar / Armar OC + Analista IA | Frontend React / BI aparte obligatorio |
| Export CSV OC (scope congelado en Agent) | Multi-agent / LangChain |
| `/replenishment/analyze` (LLM interpreta, Python calcula) | LLM calcula qty o filtra filas |

## Documentación / SDD

| Artefacto | Contenido |
|-----------|-----------|
| [`openspec/config.yaml`](openspec/config.yaml) | Strict TDD + stack |
| [`openspec/changes/interactive-drilldown/`](openspec/changes/interactive-drilldown/) | Slice API + scope + chips Python |
| [`openspec/changes/engineering-quality/`](openspec/changes/engineering-quality/) | CI, seguridad OWASP mínima, trazabilidad |
| [`openspec/changes/dual-surface-analytics/`](openspec/changes/dual-surface-analytics/) | Métricas + dashboard en chat |
| [`docs/api-simulada.md`](docs/api-simulada.md) | Contrato CSV |

**Estado:** asistente + panel de reposición recortable; qty y filtros en Python; LLM solo en la pregunta libre.

## Tests

```bash
pip install -e ".[dev]"
pytest
pytest -m performance   # smoke de rendimiento (main CI)
```

CI (GitHub Actions): pytest + cobertura ≥85% en módulos críticos + Docker smoke.

## Calidad y mantenimiento

| Doc | Contenido |
|-----|-----------|
| [`docs/maintenance-policy.md`](docs/maintenance-policy.md) | Leyes de Lehman, sprint preventivo |
| [`docs/beta-test-protocol.md`](docs/beta-test-protocol.md) | Escenario beta + checklist UX |
| [`docs/security-audit-osstmm-lite.md`](docs/security-audit-osstmm-lite.md) | Auditoría web lite |
| [`docs/compatibility-matrix.md`](docs/compatibility-matrix.md) | Browsers / SO |
| [`openspec/changes/engineering-quality/traceability-matrix.md`](openspec/changes/engineering-quality/traceability-matrix.md) | MUST → test |

## Docker (API)

```bash
docker build -t supplymate .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=gsk-... -e LLM_PROVIDER=groq supplymate
```

## Licencia

Uso educativo / portfolio salvo que se indique lo contrario en el repo.
