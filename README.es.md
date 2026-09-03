# SupplyMate

*Español* · [English](README.md)

MVP de AI Engineering para reabastecimiento en pymes de distribución.

**Principio:** *LLM orchestrates, deterministic code decides.*

*Términos técnicos en inglés a propósito (como en el código): slice, SKU, ROP, tools, qty, insight, commit.*

## Por qué existe

Una pyme de distribución necesita:

> ¿Cuánto debería pedir del producto X para cubrir los próximos 7 días?

Si el LLM inventa el stock, las ventas o la cantidad, el sistema no es confiable. SupplyMate separa roles:

- el **LLM orquesta** (intención, explicación, insight)
- el **código Python decide** (fórmula, filtros, CSV)

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
| CSVs en [`data/`](data/) | Catálogo simulado (~13k SKUs) |
| [`app/services/metrics.py`](app/services/metrics.py) | Contratos de métricas + cobertura + salud + prioridad |
| 3 tools + [`app/core/replenishment.py`](app/core/replenishment.py) | Inventario / ventas / params; qty en Python |
| Roles LLM | Intent, explainer de SKU, insight (Explorar), commit (Armar OC) |
| REST | search, replenishment, `/chat`, `/slice`, `/analyze`, dashboard, CSV |
| Streamlit | Chat + **Explorar** / **Armar OC** + Analista IA |

### Política de reposición (honesta)

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

Detalle: [`docs/contract/architecture.es.md`](docs/contract/architecture.es.md)

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
git clone https://github.com/javi2481/SupplyMate.git
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

### El flujo (menos de 2 minutos)

1. Preguntá: **¿Qué productos tengo que comprar?**
2. Click **Riesgo de quiebre** → click una categoría → seleccioná un SKU
3. Mirá el cálculo (Python, no el LLM) — *Hechos calculados por Python*
4. **Listo — armar OC** → exportá el CSV de ese recorte

Clicks, filtros y CSV = **0 llamadas al LLM**. El modelo entra en la pregunta libre, el insight del recorte y el resumen de OC.

SKU demo: `6033436`. Vocabulario: Riesgo de quiebre, Falta de stock, Sobrestock, Cobertura, Cantidad recomendada.

Ejemplos:

- `¿Cuánto debería pedir de 6033436?` → qty + **Cómo se calculó**
- `¿Qué productos tengo que comprar?` → panel **Explorar** → recorte → **Armar OC** → **Exportar OC**

```bash
curl -s -X POST http://127.0.0.1:8000/replenishment/analyze \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"explore\",\"scope\":{},\"events\":[],\"root_question\":\"¿Qué comprar?\"}"
```

Primer resultado verificable:

```bash
curl -s http://127.0.0.1:8000/products/6033436/replenishment
# → recommended_quantity: 173
```

## Flujo en terminal

**Camino SKU**

```text
Pregunta: ¿Cuánto debería pedir de 6033436?
   ↓
Intent → 3 tools → calculate_replenishment
   ↓
Respuesta: qty 173 + Cómo se calculó (validado)
```

**Camino slice**

```text
Pregunta: ¿Qué productos tengo que comprar?
   ↓
Panel Explorar → clicks (0 LLM) → Armar OC → CSV
   ↓
Si el insight LLM falla → fallback determinístico
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

## UI Streamlit opcional

Chat + **Explorar** / **Armar OC** en http://localhost:8501. La API en `:8000` es el runtime; Streamlit es la superficie de demo.

Docker (solo API):

```bash
docker build -t supplymate .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=gsk-... -e LLM_PROVIDER=groq supplymate
```

## Documentación

| Doc | Contenido |
|-----|-----------|
| [`docs/README.md`](docs/README.md) | Índice de docs (contrato / operaciones / plantillas) |
| [`app/README.md`](app/README.md) | Capas del código de aplicación |
| [`tests/README.md`](tests/README.md) | Capas de la suite de tests |
| [`docs/contract/architecture.es.md`](docs/contract/architecture.es.md) | Frontera LLM vs Python, tools, slice/scope, layout |
| [`docs/contract/evaluation.es.md`](docs/contract/evaluation.es.md) | CI, goldens, markers pytest, rendimiento |
| [`docs/contract/data-contract.es.md`](docs/contract/data-contract.es.md) | Contrato CSV / `product_id` |

SDD interno: [`openspec/`](openspec/) (specs por change; no es la puerta de entrada).

### Calidad y mantenimiento

| Doc | Contenido |
|-----|-----------|
| [`docs/operations/maintenance-policy.md`](docs/operations/maintenance-policy.md) | Leyes de Lehman, sprint preventivo |
| [`docs/operations/beta-test-protocol.md`](docs/operations/beta-test-protocol.md) | Escenario beta + checklist UX |
| [`docs/operations/security-audit-osstmm-lite.md`](docs/operations/security-audit-osstmm-lite.md) | Auditoría web lite |
| [`docs/operations/compatibility-matrix.md`](docs/operations/compatibility-matrix.md) | Browsers / SO |
| [`docs/operations/performance-profile.md`](docs/operations/performance-profile.md) | Umbrales smoke de rendimiento |
| [`openspec/changes/engineering-quality/traceability-matrix.md`](openspec/changes/engineering-quality/traceability-matrix.md) | MUST → test |

**Estado:** v0.1 — asistente + panel de reposición recortable; qty y filtros en Python; LLM solo en pregunta libre / insight / commit.

### Próximos hitos

1. **Segundo origen de catálogo** — validar el contrato CSV con otro dataset
2. **Auth en API** — endpoints listos para despliegue controlado
3. **Interpretación de consulta** — endurecer goldens multiturn y referencias
4. **Export enriquecido** — formatos de OC más allá del CSV base

## Contribuciones

Contribuciones bienvenidas — ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Salud del repositorio

[![CI](https://github.com/javi2481/SupplyMate/actions/workflows/ci.yml/badge.svg)](https://github.com/javi2481/SupplyMate/actions/workflows/ci.yml)

CI ejecuta `pytest -m "not performance and not llm"`, cobertura ≥85% en módulos críticos, y Docker smoke. Marker `llm` excluido del CI principal.

```bash
pytest -m "not performance and not llm"
pytest -m performance   # smoke de rendimiento (main CI)
# Live Groq (no CI): RUN_LLM_EVALS=1 pytest -m llm
```

## Licencia

MIT — ver [`LICENSE`](LICENSE).
