# Perfil operativo — rendimiento

Catálogo demo: ~13 000 SKUs (CSV en `data/`).

## Mix de carga esperado (MVP)

| Operación | Peso | Endpoint / función |
|-----------|------|---------------------|
| Lectura slice / dashboard | ~90% | `GET /replenishment/slice`, `chat_dashboard()` |
| Chat LLM | ~10% | `POST /chat` |

## Umbrales smoke (`tests/test_performance.py`)

| Operación | Umbral CI |
|-----------|-----------|
| `replenishment_slice(limit=100)` | < 3 s |
| `chat_dashboard(limit=100)` | < 3 s |

Job `performance` en CI solo en rama `main`.

## Notas

- Primera carga construye `_sku_rows_cache` — incluida en medición.
- No incluye latencia Groq (chat mock en tests).
