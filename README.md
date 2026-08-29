# SupplyMate

MVP de AI Engineering para reabastecimiento en pymes de distribución.

**Principio:** *LLM orchestrates, deterministic code decides.*

## Por qué existe

Una pyme de distribución necesita responder:

> ¿Cuánto debería pedir del producto X para cubrir los próximos 7 días?

Si el LLM inventa el stock, las ventas o la cantidad a pedir, el sistema no es confiable. SupplyMate separa roles:

- el **LLM orquesta** (elige tools y explica)
- el **código Python decide** (fórmula determinística de reabastecimiento)

Así la cantidad recomendada es testeable, reproducible y explicable en una entrevista de AI Engineering — sin RAG, sin embeddings y sin multi-agent.

## Para quién es

- **AI / ML engineers** que quieren un caso claro de *tool-calling + lógica determinística*
- **Equipos de operaciones / supply** que necesitan una recomendación concreta, no un párrafo ambiguo
- **Candidatos a entrevistas** que buscan un MVP chico, testeable y fácil de narrar

## ¿Por qué no usar X?

| Alternativa | Por qué no en este MVP |
|-------------|-------------------------|
| **RAG / embeddings / vector DB** | Los datos ya son CSV estructurados; no hay documentos que recuperar |
| **LangChain / LangGraph** | Overkill para 1 agente + 3 tools; usamos OpenAI Agents SDK |
| **Que el LLM calcule** | Los números críticos no deben alucinarse; Python calcula |
| **Multi-agent / handoffs** | Un solo agente alcanza para esta pregunta |
| **Forecasting / ML / EOQ** | Fuera de scope; la fórmula es explícita y simple |
| **Voyage / embeddings APIs** | Útiles para retrieval, no para orquestar tools ni explicar pedidos |

## Cómo funciona SupplyMate

```text
User
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
| CSVs en [`data/`](data/) | **API simulada** (~13k SKUs): products, prices, inventory, sales, params |
| [`docs/api-simulada.md`](docs/api-simulada.md) | Contrato de datos + regeneración desde xlsx |
| [`app/store.py`](app/store.py) | Carga in-memory de los 5 recursos → `ProductMaster` |
| [`app/services/catalog_service.py`](app/services/catalog_service.py) | Ficha + recomendación determinística |
| 3 tools | `get_inventory`, `get_sales_history`, `get_replenishment_params` |
| [`app/replenishment.py`](app/replenishment.py) | Fórmula 7 días (Python decide qty) |
| REST | `/products/search`, `/products/{id}`, `/products/{id}/replenishment`, `/chat` |
| Streamlit | Demo conversacional sobre `/chat` |

**Fórmula:**

```text
avg_daily      = total_units_sold_last_30 / 30
demand_horizon = avg_daily * 7
demand_lead    = avg_daily * lead_time_days
stock_target   = demand_horizon + demand_lead + safety_stock
recommended    = max(0, stock_target - current_stock)
```

Detalle de diseño: [`openspec/changes/mvp-core/`](openspec/changes/mvp-core/) + [`openspec/changes/catalog-integration/tasks.md`](openspec/changes/catalog-integration/tasks.md).

## Qué demuestra el MVP

**Catálogo real** — `6033436` → qty **172**; `8141600` → qty **0**.

La cantidad sale de Python. El LLM solo explica. Precios y punto de quiebre son contexto, no entran en la fórmula.

## Qué trae el clone

| Listo al clonar | Opcional |
|-----------------|----------|
| CSVs recurso en [`data/`](data/) (~13k SKUs) | Key de Groq en `.env` (gratis) |
| Dump origen [`docs/perfumeria_enriched.xlsx`](docs/perfumeria_enriched.xlsx) | Re-export: `python scripts/export_catalog_csvs.py` |
| Tests pytest usan [`data/`](data/) | UI Streamlit |
| FastAPI + agente + fórmula | Docker |
| Artefactos SDD en [`openspec/`](openspec/) | OpenAI pago |

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

Abrí http://localhost:8501 y preguntá por un código del catálogo, p.ej.:

`¿Cuánto debería pedir de 6033436?`

## Flujo en terminal

**Camino recomendación**

```text
Pregunta: ¿Cuánto debería pedir de 6033436?
   ↓
Agent elige tools (inventory / sales / params)
   ↓
SupplyContext listo
   ↓
Python calculate_replenishment → recommended_quantity = 172
   ↓
LLM explica en español usando ese JSON
   ↓
POST /chat → { answer, product_id, recommended_quantity }
```

**Camino producto inexistente**

```text
Pregunta: ¿Cuánto pedir de 99999999?
   ↓
Tools / contexto incompleto
   ↓
404 Product not found
```

Ejemplo HTTP (REST determinístico, sin LLM):

```bash
curl -s http://127.0.0.1:8000/health

curl -s "http://127.0.0.1:8000/products/search?q=47%20street"

curl -s http://127.0.0.1:8000/products/6033436/replenishment

curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"¿Cuánto debería pedir de 6033436?\"}"
```

PowerShell: `scripts/demo_queries.ps1`

## Alcance

| Incluido | Excluido |
|----------|----------|
| 1 agente + 3 tools | RAG, embeddings, vector DB |
| Cálculo determinístico | Forecasting / ML / EOQ |
| Catálogo CSV (~13k) + servicio unificado | Base de datos |
| FastAPI + pytest + Docker | Kubernetes / compose complejo |
| Streamlit UI liviana | Frontend React / Open WebUI / LibreChat |
| Groq free tier | Multi-agent / LangChain |
| Semántica in-memory (catálogos chicos) | Vector DB / RAG documental |
| SDD (`openspec`) + Strict TDD | Sessions / historial de chat |

## UI opcional (Streamlit)

No hace falta para validar la lógica (alcanza pytest + `/docs`). La UI solo consume `POST /chat`.

```bash
# Terminal 1
uvicorn app.api:app --host 127.0.0.1 --port 8000

# Terminal 2
streamlit run ui/streamlit_app.py
```

Variables útiles en `.env`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-20b
SUPPLYMATE_API_URL=http://127.0.0.1:8000
```

## Documentación / SDD

| Artefacto | Contenido |
|-----------|-----------|
| [`openspec/config.yaml`](openspec/config.yaml) | Strict TDD + stack |
| [`openspec/changes/mvp-core/proposal.md`](openspec/changes/mvp-core/proposal.md) | Por qué / qué |
| [`openspec/changes/mvp-core/design.md`](openspec/changes/mvp-core/design.md) | Arquitectura |
| [`openspec/changes/mvp-core/specs/`](openspec/changes/mvp-core/specs/) | Escenarios Given/When/Then |
| [`openspec/changes/mvp-core/tasks.md`](openspec/changes/mvp-core/tasks.md) | Tasks de apply |
| [`openspec/changes/mvp-core/verify-report.md`](openspec/changes/mvp-core/verify-report.md) | Evidencia TDD |

**Estado:** producto integrado — maestro CSV + REST determinístico + agente 3 tools + Streamlit + Docker.

### Próximos hitos (opcional)

1. Auth mínima en `/chat`
2. Tracing Groq/OpenAI para demos
3. Compose API + Streamlit

## Tests

```bash
pip install -e ".[dev]"
pytest
```

La lógica determinística y las tools CSV corren **sin** llamar al LLM. El agente se mockea.

## Docker

```bash
docker build -t supplymate .
docker run --rm -p 8000:8000 -e GROQ_API_KEY=gsk-... -e LLM_PROVIDER=groq supplymate
```

## Licencia

Uso educativo / portfolio salvo que se indique lo contrario en el repo.
