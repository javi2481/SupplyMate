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
| [`app/services/analytics/metrics.py`](app/services/analytics/metrics.py) | Contratos de métricas + cobertura + salud + prioridad |
| 3 tools + [`app/core/replenishment.py`](app/core/replenishment.py) | Inventario / ventas / params; qty en Python |
| Roles LLM | Intent, explainer de SKU, insight (Explorar); resumen commit opcional |
| REST | search, replenishment, `/chat`, `/slice`, `/analyze`, dashboard, CSV |
| Frontend Vite (`frontend/`) | UI viva: chat + **Explorar** / **Revisar OC** |

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

**Catálogo real** — `6033436` → qty **173**; `8141600` → **0**. Carrito operator-driven → Revisar OC → CSV con **selector de columnas** (default `barcode` + `order_quantity`; opcionales id/nombre, categoría, proveedor, sugerida, valor estimado). Valor de compra = qty × precio de lista (no PVP).

Verdad del panel: KPIs / chart / tabla vienen de `GET /replenishment/slice` para el scope activo (ver [`docs/operations/recorte-coherence.md`](docs/operations/recorte-coherence.md)).

### Capturas

![Panel Explorar — chat + KPIs + chart](docs/assets/explore-panel.png)

![Revisar OC — columnas del export](docs/assets/oc-export-columns.png)

## Qué trae el clone

| Listo al clonar | Opcional |
|-----------------|----------|
| CSVs en [`data/`](data/) | `GROQ_API_KEY` en `.env` (o DeepSeek / OpenAI) |
| Tests pytest | OpenAI pago |
| FastAPI + agente + fórmula | |
| Frontend Vite (`frontend/`) | |

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
cd frontend
cp .env.example .env   # VITE_SUPPLYMATE_API_URL=http://127.0.0.1:8000
npm install
npm run dev -- --host 127.0.0.1 --port 8080
```

Abrí **http://127.0.0.1:8080**. Si el puerto `8000` ya está ocupado, corré la API en `8001` y ajustá `VITE_SUPPLYMATE_API_URL`.

Smoke de API (con uvicorn en :8000):

```powershell
.\scripts\smoke_api.ps1
```

### El flujo (menos de 2 minutos)

1. Preguntá: **¿Qué productos tengo que comprar?**
2. Click en un **chip de salud** o una **barra del chart** → refiná el recorte (KPIs/tabla siguen `/slice`)
3. **Agregar al pedido** en los SKUs que quieras (el chat sugiere; el operador decide)
4. Abrí **Revisar OC** → ajustá cantidades → **Exportar y terminar** → elegí columnas del CSV (barcode + qty por defecto)

Clicks, filtros y CSV = **0 llamadas al LLM**. El modelo entra en la pregunta libre y la explicación de un SKU.

SKU demo: `6033436`. Vocabulario: Riesgo de quiebre, Falta de stock, Sobrestock, Cobertura, Cantidad recomendada.

Ejemplos:

- `¿Cuánto debería pedir de 6033436?` → qty + **Cómo se calculó**
- `¿Qué productos tengo que comprar?` → **Explorar** → agregar líneas → **Revisar OC** → **Exportar CSV**

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

**Camino slice + carrito**

```text
Pregunta: ¿Qué productos tengo que comprar?
   ↓
Panel Explorar → clicks (0 LLM) → Agregar al pedido → Revisar OC → columnas CSV
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
| UI Vite Explorar / Revisar OC | BI aparte obligatorio |
| Carrito operator-driven + CSV con columnas | Multi-agent swarm / LangChain |
| `/replenishment/analyze` (LLM interpreta, Python calcula; API de insight opcional) | LLM calcula qty o filtra filas |
| Evals de insight + golden intents (CI sin LLM live) | LangSmith / OpenTelemetry |

## UI viva

Chat + **Explorar** / **Revisar OC** en http://127.0.0.1:8080 contra la API en `:8000`. Ver [`frontend/README.md`](frontend/README.md).

El scaffold de UI nació en Lovable; la superficie de producto es esta app Vite en `frontend/`.

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
| [`docs/operations/recorte-coherence.md`](docs/operations/recorte-coherence.md) | Dueño del panel + seis invariantes de coherencia |
| [`docs/operations/maintenance-policy.md`](docs/operations/maintenance-policy.md) | Leyes de Lehman, sprint preventivo |
| [`docs/operations/beta-test-protocol.md`](docs/operations/beta-test-protocol.md) | Escenario beta + checklist UX |
| [`docs/operations/security-audit-osstmm-lite.md`](docs/operations/security-audit-osstmm-lite.md) | Auditoría web lite |
| [`docs/operations/compatibility-matrix.md`](docs/operations/compatibility-matrix.md) | Browsers / SO |
| [`docs/operations/performance-profile.md`](docs/operations/performance-profile.md) | Umbrales smoke de rendimiento |
| [`openspec/changes/archive/2026-09-10-engineering-quality/traceability-matrix.md`](openspec/changes/archive/2026-09-10-engineering-quality/traceability-matrix.md) | MUST → test (archivado) |

**Estado:** v0.5.0 — reposición conversacional + panel Explorar recortable; qty y filtros en Python; carrito OC operator-driven; LLM en pregunta libre / insight.

### Decisiones de diseño (listas para entrevista)

1. **Los números nunca salen del modelo** — `calculate_replenishment()` es dueño de la qty; el LLM narra hechos validados.
2. **Un solo dueño del panel** — `/replenishment/slice` para el `UiSlice` activo; el chat board solo es placeholder de carga.
3. **El operador es dueño de la OC** — el chat sugiere; el humano agrega líneas, edita qty y elige columnas del CSV.

### Próximos hitos

1. **Segundo origen de catálogo** — validar el contrato CSV con otro dataset
2. **Auth en API** — endpoints listos para despliegue controlado
3. **Interpretación de consulta** — endurecer goldens multiturn y referencias
4. **Formatos de OC más ricos** — plantillas ERP más allá del picker (EDI, XLSX, etc.)

## Contribuciones

Contribuciones bienvenidas — ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Salud del repositorio

[![CI](https://github.com/javi2481/SupplyMate/actions/workflows/ci.yml/badge.svg)](https://github.com/javi2481/SupplyMate/actions/workflows/ci.yml)

CI ejecuta `pytest -m "not performance and not llm"`, cobertura ≥85% en módulos críticos, y Docker smoke. Marker `llm` excluido del CI principal.

```bash
pytest -m "not performance and not llm"
pytest -m performance   # smoke de rendimiento (main CI)
# Evals LLM paraphrase (no CI): RUN_LLM_EVALS=1 pytest -m llm
```

## Licencia

MIT — ver [`LICENSE`](LICENSE).
