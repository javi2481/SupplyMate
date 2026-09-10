# Estado de superficies — FastAPI + Lovable

Fecha: 10 sep 2026 (actualizado: Streamlit retirado del repo).

## Veredictos

| Pregunta | Respuesta |
|----------|-----------|
| ¿UI de producto? | **Vite** (`npm run dev`, típicamente `:8080`) + FastAPI (`uvicorn :8000`). |
| ¿El front está cableado al back? | **Sí**: slice, chat, SKU y CSV. |
| ¿El LLM funciona? | **Sí, en su rol.** Texto libre ambiguo, explicación de SKU; insight `/analyze` existe en API pero **no** lo llama el frontend Lovable. |

## Runtime

- FastAPI: `uvicorn app.api:app --host 127.0.0.1 --port 8000`
- Frontend: `npm run dev` en `frontend/` (Vite, puerto Lovable **8080**)

## Cableado front → back

| UI | Endpoint | Uso |
|----|----------|-----|
| Panel Explorar (KPIs, tabla, gráfico, chips) | `GET /replenishment/slice` | `useSlice` → `fetchSlice` |
| Pregunta del chat | `POST /chat` | `postChat` + `applyChatScope` |
| Detalle SKU | `GET /products/{id}/replenishment` | `fetchReplenishment` |
| Export OC | `GET /replenishment/purchase-list.csv` | `purchaseListCsvUrl` |
| Chips del composer | `suggested_filters` del slice | `applySuggestedFilter` (sin chat) |
| Insight | `POST /replenishment/analyze` | API pública; no llamada por Lovable |

E2E local opcional: `scripts/e2e_ui_chats.py` / `scripts/e2e_validation_chats.py` (extra `pip install -e ".[e2e]"`).
