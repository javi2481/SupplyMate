# SupplyMate

MVP de AI Engineering para reabastecimiento en pymes de distribución.

**Principio:** *LLM orchestrates, deterministic code decides.*

## El flujo (menos de 2 minutos)

1. Preguntá: **¿Qué productos tengo que comprar?**
2. Click **Riesgo de quiebre** → click una categoría → seleccioná un SKU
3. Mirá el cálculo (Python, no el LLM) — *Hechos calculados por Python*
4. **Listo — armar OC** → exportá el CSV de esa recorte

Clicks, filtros y CSV = **0 llamadas al LLM**. El modelo entra en la pregunta libre, el insight del recorte y el resumen de OC.

SKU demo: `6033436`. Vocabulario: Riesgo de quiebre, Falta de stock, Sobrestock, Cobertura, Cantidad recomendada.

## Por qué existe

Una pyme de distribución necesita:

> ¿Cuánto debería pedir del producto X para cubrir los próximos 7 días?

Si el LLM inventa el stock, las ventas o la cantidad, el sistema no es confiable. SupplyMate separa roles:

- el **LLM orquesta** (intención, explicación, insight)
- el **código Python decide** (fórmula, filtros, CSV)

## Política de reposición (honesta)

**Order-up-to / periodic review**

```text
avg_daily      = total_units_sold_last_30 / 30
demand_horizon = avg_daily * 7
demand_lead    = avg_daily * lead_time_days
stock_target   = demand_horizon + demand_lead + safety_stock
recommended    = max(0, ceil(stock_target - current_stock))
```

- **Punto de reorden** es una alarma de salud (pinta “Riesgo de quiebre”). No entra en la cantidad a pedir.
- **Cobertura** = stock / demanda diaria 30d. Aproximación, no un forecast.
- **Riesgo de quiebre** = regla (`qty > 0` y stock ≤ ROP). No es una probabilidad.
- **Sobrestock** = stock > máximo y qty = 0. No es dead stock.
- Las ventas diarias del historial se **expanden de forma uniforme** a partir del total 30d. No hay serie temporal real: no infieras tendencia ni estacionalidad.

No es un modelo de demanda ML. El MVP demuestra reposición determinística + analítica conversacional.

## Para quién es

- **Applied AI engineers** que quieren un caso de *tool-calling + lógica determinística + insights validados*
- **Operaciones / supply** que necesitan una OC exportable sobre el mismo recorte que ven
- **Entrevistas** — MVP chico, testeable, fácil de narrar

## ¿Por qué no usar X?

| Alternativa | Por qué no en este MVP |
|-------------|-------------------------|
| **RAG / embeddings / vector DB** | CSV estructurado; matching lexical de SKU. Sin modelos de embeddings en runtime. |
| **LangChain / LangGraph** | Overkill para 3 tools de inventario; OpenAI Agents SDK |
| **Que el LLM calcule** | Los números críticos no se alucinan; Python calcula y valida la narración |
| **Multi-agent swarm** | Roles LLM separados (intent / explain / insight / commit), no un enjambre |
| **Forecasting / ML / EOQ** | Fuera de scope; la política es explícita y simple |
| **Postgres / dbt / Airflow / Superset** | Overkill; el dashboard vive en el chat |

## Cómo funciona

```text
User
  ↓
/chat  ── regex o clasificador de intención
  ├── lista / dashboard  → slice Python (0 LLM en cada click)
  └── un SKU             → 3 tools → calculate_replenishment → explicación (validada)
/replenishment/slice     → mismos filtros que el CSV
/replenishment/analyze   → insight o resumen OC, validator, fallback determinístico
```

| Pieza | Rol |
|-------|-----|
| CSVs en [`data/`](data/) | **API simulada** (~13k SKUs) |
| [`app/services/metrics.py`](app/services/metrics.py) | Contratos de métricas + cobertura + salud + prioridad |
| 3 tools + [`app/replenishment.py`](app/replenishment.py) | Inventario / ventas / params; qty en Python |
| Roles LLM | Intent, explainer de SKU, insight (Explorar), commit (Armar OC) |
| REST | search, replenishment, `/chat`, `/slice`, `/analyze`, dashboard, CSV |
| Streamlit | Chat + **Explorar** / **Armar OC** + Analista IA |

SDD: [`openspec/changes/mvp-core/`](openspec/changes/mvp-core/) + dual-surface + interactive-drilldown + llm-drilldown-insights + [`semantic-correctness`](openspec/changes/semantic-correctness/).

## Qué demuestra el MVP

**Catálogo real** — `6033436` → qty **173**; `8141600` → **0**. Lista de compras + CSV OC (`barcode,product_id,product_name,supplier,recommended_quantity,operational_priority,estimated_purchase_value`). Valor de compra = qty × precio de lista (no PVP).

## Qué trae el clone

| Listo al clonar | Opcional |
|-----------------|----------|
| CSVs en [`data/`](data/) | `GROQ_API_KEY` en `.env` |
| Tests pytest | Streamlit |
| FastAPI + agente + fórmula | OpenAI pago |

## Inicio rápido

```bash
git clone <este-repo>
cd SupplyMate
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Editar .env y poner GROQ_API_KEY (https://console.groq.com/keys)

pytest -m "not performance and not llm"
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
- `¿Qué productos tengo que comprar?` → panel **Explorar** → recorte → **Armar OC** → **Exportar OC**

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
| 3 tools de inventario + roles LLM acotados | RAG, embeddings, vector DB |
| Cálculo determinístico order-up-to | Forecasting / ML / EOQ |
| Catálogo CSV | Postgres app DB / dbt / Airflow / Superset |
| Streamlit Explorar / Armar OC + Analista IA | Frontend React / BI aparte obligatorio |
| Export CSV OC (scope congelado en Agent) | Multi-agent swarm / LangChain |
| `/replenishment/analyze` (LLM interpreta, Python calcula) | LLM calcula qty o filtra filas |
| Evals de insight + golden intents (CI sin Groq live) | LangSmith / OpenTelemetry |

## Documentación / SDD

| Artefacto | Contenido |
|-----------|-----------|
| [`openspec/config.yaml`](openspec/config.yaml) | Strict TDD + stack |
| [`openspec/changes/semantic-correctness/`](openspec/changes/semantic-correctness/) | Política, perímetro, evals, valor de compra |
| [`openspec/changes/interactive-drilldown/`](openspec/changes/interactive-drilldown/) | Slice API + scope + chips Python |
| [`openspec/changes/engineering-quality/`](openspec/changes/engineering-quality/) | CI, seguridad OWASP mínima, trazabilidad |
| [`openspec/changes/dual-surface-analytics/`](openspec/changes/dual-surface-analytics/) | Métricas + dashboard en chat |
| [`docs/api-simulada.md`](docs/api-simulada.md) | Contrato CSV |

**Estado:** asistente + panel de reposición recortable; qty y filtros en Python; LLM solo en pregunta libre / insight / commit.

## Tests

```bash
pip install -e ".[dev]"
pytest -m "not performance and not llm"
pytest -m performance   # smoke de rendimiento (main CI)
# Live Groq (no CI): RUN_LLM_EVALS=1 pytest -m llm
```

CI (GitHub Actions): pytest + cobertura ≥85% en módulos críticos + Docker smoke. Marker `llm` excluido.

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
