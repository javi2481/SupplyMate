# Estado de superficies — FastAPI + Lovable vs Streamlit

Fecha: 10 sep 2026. Investigación de runtime y cableado. Sin cambio de código de producto.

## Veredictos

| Pregunta | Respuesta |
|----------|-----------|
| ¿Usamos Streamlit en el producto vivo? | **No.** Vite (`npm run dev`) + FastAPI (`uvicorn :8000`). Streamlit sigue en el repo como leftover. |
| ¿El front está cableado al back? | **Sí**, para slice, chat, SKU y CSV. Los números de la captura (409 / 114 / 6.915) salen de `/replenishment/slice` y del `scope` de `/chat`. |
| ¿El LLM funciona? | **Sí, en su rol.** No escribe el texto de esa burbuja. «desodorantes» lo resuelven reglas. El LLM entra en texto libre ambiguo, explicación de SKU, e insight `/analyze` (este último **no** lo llama el front Lovable). |

## Runtime observado

Terminales activos del workspace:

- FastAPI: `uvicorn app.api:app --reload --host 127.0.0.1 --port 8000`
- Frontend: `npm run dev` en `frontend/` (Vite)
- Ningún `streamlit run`

## Qué queda de Streamlit (no es el camino del operador)

Sigue existiendo: `ui/streamlit_app.py`, `pyproject.toml` (`streamlit>=1.57.0`), tests AppTest, README / `docs/contract/architecture.es.md` que todavía listan puerto 8501 como UI.

Eso es **docs y código viejo**, no la captura de Explorar / Revisar OC.

## Cableado front → back

| UI | Endpoint | Uso |
|----|----------|-----|
| Panel Explorar (KPIs, tabla, gráfico, chips) | `GET /replenishment/slice` | `useSlice` → `fetchSlice` |
| Pregunta del chat | `POST /chat` | `postChat(message, scope)`; `applyChatScope` aplica `ChatResponse.scope` |
| Detalle SKU | `GET /products/{id}/replenishment` | `fetchReplenishment` |
| Export OC | `GET /replenishment/purchase-list.csv` | `purchaseListCsvUrl` |
| Chips del composer | `suggested_filters` del slice | Click local (`applySuggestedFilter`); no manda `ChatRequest.chip` |
| Analista IA / insight | `POST /replenishment/analyze` | **No llamado** por el frontend Lovable (sí por Streamlit) |

`ChatResponse` en Python trae `interpretation`, `group_summaries`, `guidance`. El tipo TS de `api.ts` **no los declara**: el chat solo pinta `answer`. Por eso las opciones de guidance se ven como markdown en el texto, duplicadas respecto de los chips del slice.

## LLM: dónde sí y dónde no

Contrato: Python decide qty. El LLM orquesta / explica.

| Camino | ¿LLM? | ¿Lo usa Lovable? |
|--------|-------|------------------|
| `que desodorantes tengo que comprar?` | No. `interpret_query_rules` (verbo comprar + referencia) → `explore` + `format_explore_answer` | Sí |
| Texto libre que las reglas no matchean | `interpret_query_llm` (Groq) | Sí, si hace falta |
| Fallback de intención | `classify_intent` | Sí, último recurso |
| Un SKU | tools + `calculate_replenishment` + explainer LLM (fallback Python si el texto no valida) | Sí, vía `/chat` |
| Insight del recorte | `run_analyze` | No en Lovable |
| Clicks de filtro / gráfico | 0 LLM | Sí |

Provider: `LLM_PROVIDER=groq` por defecto (`app/core/config.py`). Sin key, el clasificador/intérprete hace fallback; las qty siguen saliendo de Python.

## Corrección al QA anterior

El markdown crudo **no** prueba que Streamlit esté corriendo. Prueba que el string de Python todavía usa `**` / `_` y que React no lo renderiza. Los números del chat y del panel **sí** están acordes: mismo motor, mismo recorte.
