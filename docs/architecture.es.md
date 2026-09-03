**Español** · [English](architecture.md) · [README](../README.md) · [README ES](../README.es.md)

# Arquitectura

Para el problema y el inicio rápido, ver el [README ES](../README.es.md). Este documento es el **contrato técnico**: frontera LLM, tools, slice/scope, superficies y layout del repo.

SupplyMate es un **asistente de reposición**, no un chat genérico. La entrada del usuario pasa por routing de intención; **Python calcula qty, filtros y CSV** antes de emitir narración del LLM.

*Términos técnicos en inglés a propósito: slice, scope, tools, qty, insight, commit.*

## Capas de fuente de verdad

| Artefacto | Rol |
|-----------|-----|
| CSVs en `data/` | Evidencia primaria del catálogo |
| `app/store.py` | Carga in-memory + `CatalogStore` |
| `ProductMaster` | Fila unificada para métricas y reposición |
| `calculate_replenishment()` | Verdad operativa de qty |
| Roles LLM | Intent, explain, insight, commit (solo narración) |
| Streamlit | UI consumidora (no fuente de verdad) |

```text
CSV → CatalogStore → ProductMaster → calculate_replenishment → REST / CSV
                                              ↑
                                    3 tools (camino agente)
```

## Frontera LLM vs Python

| Concern | Dueño |
|---------|-------|
| `recommended_quantity` | Python (`app/replenishment.py`) |
| Filtros slice, KPIs dashboard | Python (`app/services/catalog_service.py`, `dashboard.py`) |
| Filas CSV OC del scope actual | Python (mismos filtros que slice) |
| Clasificación de intención | Regex + clasificador; LLM para texto libre ambiguo |
| Prosa de explicación SKU | LLM, validada contra hechos Python |
| Insight Explorar / resumen Armar OC | LLM + `insight_validator`; fallback determinístico si falla |

**Python decide qty. El LLM explica y resume.**

## Superficie de tools

Tres tools del OpenAI Agents SDK en [`app/tools.py`](../app/tools.py):

| Tool | Devuelve |
|------|----------|
| `get_inventory` | `current_stock` |
| `get_sales_history` | unidades vendidas 30d (expansión diaria uniforme en store) |
| `get_replenishment_params` | `lead_time_days`, `safety_stock` |

Flujo agente para un SKU: tools llenan `SupplyContext` → `calculate_replenishment()` → explicación validada.

Constantes de política: `HORIZON_DAYS = 7`, `HISTORY_DAYS = 30`, nombre `order-up-to`. Ver [`app/replenishment.py`](../app/replenishment.py).

## Slice y scope

- **`GET /replenishment/slice`** — filas SKU filtradas; mismos predicados que el CSV de compra.
- **`AnalyticalScope`** — categoría, proveedor, chips de salud, banda de cobertura; congelado al armar OC.
- **Clicks en Streamlit Explorar** — actualizan scope en Python; **0 llamadas LLM** por click de filtro.

[`app/services/scope.py`](../app/services/scope.py) sanitiza payloads de scope. [`app/scope_builder.py`](../app/scope_builder.py) fusiona eventos UI en scope.

## Superficies

| Superficie | Puerto | Rol |
|------------|--------|-----|
| FastAPI | 8000 | Runtime: `/chat`, `/replenishment/*`, `/products/*` |
| Streamlit | 8501 | Chat + Explorar + Armar OC + Analista IA |
| Imagen Docker | 8000 | Solo API (`COPY app`, `COPY data`; Streamlit fuera de imagen) |

Endpoints clave:

- `POST /chat` — router de intención + agente
- `GET /replenishment/slice` — tabla dashboard
- `POST /replenishment/analyze` — insight explore o resumen commit
- `GET /replenishment/purchase-list.csv` — export OC del scope actual

## Layout del repo

| Path | Rol |
|------|-----|
| `app/api.py` | App FastAPI + middleware |
| `app/agent.py` | Agentes: supply, explain, insight, commit |
| `app/replenishment.py` | Fórmula order-up-to |
| `app/tools.py` | 3 tools de inventario |
| `app/services/` | catalog, dashboard, metrics, scope, insight validator |
| `app/middleware/` | rate limit, safe errors, security headers |
| `ui/` | App Streamlit |
| `data/` | CSVs por recurso (ver [data-contract.es.md](data-contract.es.md)) |
| `tests/` | pytest + goldens CSV |
| `openspec/` | SDD interno (specs strict TDD por change) |

Las specs internas viven en `openspec/changes/` — no son el índice público del README.
