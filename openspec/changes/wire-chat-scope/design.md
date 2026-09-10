# Design: Wire chat scope

## Technical Approach

Python already returns `ChatResponse.scope` from `build_scope` / `_run_explore` / `_run_purchase_list`. Explore must treat that payload as the recorte.

```
send(message)
  → POST /chat { message, scope: current chrome }
  → on 200: UiSlice = scopePayloadToUiSlice(res.scope)  // replace
            buyOnly if res.mode === "list"
            open drawer if product_id / highlight_product_id
            assistant text = res.answer
  → on 404: keep UiSlice; “No encontré «{message}» en el catálogo.”
  → else: keep UiSlice; “No pude cargar el catálogo. Intentá de nuevo en un momento.”
```

`useSlice(sliceToScopeQuery(uiSlice))` already refetches. Do not paint `res.dashboard` as a second source of truth.

## scopePayloadToUiSlice

Replace, not merge: missing/empty `categories` clears `cats`. Map:

- `health_buckets` stockout_risk/overstock → tags; `out_of_stock_only` → `sin_stock` + `outOfStockOnly`
- `coverage_buckets[0]` if in `COVERAGE_ORDER`
- `suppliers`, `name_tokens`, `subcategories`, `highlight_product_id`
- `buyOnly` is not on AnalyticalScope; set from `mode === "list"` in `applyChatScope`
- `scope === null` → keep current UiSlice (single SKU / no new recorte)

`sliceToScopeQuery` / `scopeQueryToPayload` MUST send name_token, subcategory, highlight, out_of_stock so GET `/slice` matches chat.

## Demo catalog removal

`useSlice.useMock` goes away. Failed or disabled fetch → empty rows, `online: false`, badge **Sin catálogo**. Chart uses `COPY_CATEGORIES_LOAD_FAILED` when `error`, else existing recorte-empty copy.

Delete `CATALOG` / `ROWS` / `compute` / `answerFor`. Keep labels, `HORIZON_DAYS`, `Calc` types. CSV export only via FastAPI URL. `mockNextStepChips` stays test-only; Index uses `suggestedFilters` only.

`preferLiveApi`: URL set → fetch. Ignore `VITE_SUPPLYMATE_USE_MOCK`.

## Index wiring

Prefer `UiSlice` + `useScope` (already unused). Drop local `Slice` / `toScopeQuery` / `applySlice(ROWS)`. `findRowForProduct`: live rows then `purchaseList`, never `ROWS`.

`getJson` throws `HttpError` with `status` so 404 is distinguishable.

## Frozen chrome

Do not split `index.tsx`. Do not add evidence/guidance/KPI cards.
