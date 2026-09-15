# Coherencia del recorte — checklist operativo

Ritual QA antes de tocar UI: mirar `logs/chat-turns.jsonl`, el campo `trace` de la respuesta, y el log de browser `[SupplyMate turn]` / `sessionStorage.supplymate.chatTurnLog`.

## Dueño único del panel

`GET /replenishment/slice` para el `UiSlice` activo es la verdad de KPIs, chart y tabla. Tras `/chat`, se aplica el scope y `useSlice` recalcula. `chatBoard` solo es placeholder mientras `api.loading`; nunca verdad durable encima de un scope ya cambiado.

Álgebra de filtros (`filter_rows`): mismo eje → OR; ejes distintos → AND.

## Seis invariantes

Tras un turno o un `mutateSlice` (chip / KPI / click de chart), estas superficies deben decir lo mismo:

| # | Superficie | Qué debe cuadrar |
|---|------------|------------------|
| 1 | Label / breadcrumb | Texto del recorte ≡ ejes del `UiSlice` activo |
| 2 | Scope | Categorías, subcategorías, health, coverage, supplier, tokens enviados a `/slice` |
| 3 | KPI | `purchase_skus`, `recommended_units`, valor — del dashboard de `/slice` |
| 4 | Chart | Barras del mismo dashboard (granularidad por forma del recorte, no por rubro hardcodeado) |
| 5 | Tabla | Filas filtradas del mismo slice |
| 6 | CTA / OC | CTA de consulta según replenishment del scope; OC solo operator-driven (chat no arma carrito; sin `draft_oc` en purchase vacío) |

Si el label cambia y los números no (o al revés), es desync de fuentes — no un “parche de frase”.

## Smoke manual mínimo

1. Chat o click que deje **Fragancias**, luego click **Nacionales** en el chart → KPIs/tabla ≈ **493** purchase SKUs / **23918** unidades (cat∩sub AND).
2. Rules-path conocido (p. ej. Biferdil) → `/chat` **&lt; 2 s** (si &gt; 5 s sin LLM → hang).
3. Tras mutar scope con panel ya cargado (`loading === false`), el panel no debe seguir mostrando el dashboard de `chatBoard`.
