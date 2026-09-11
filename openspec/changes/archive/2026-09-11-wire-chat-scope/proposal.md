# Proposal: Wire chat scope

## Intent

Explore guesses the recorte from chat text (`sliceFromText`) and ignores `ChatResponse.scope`. If `/chat` fails it narrates the Lovable demo catalog (`ROWS` / `answerFor`). The operator must see `/data` only: Python interprets, the board follows `scope`, and empty/not-found states speak in catalog copy — never demo SKUs.

## Scope

### In Scope
- Apply `ChatResponse.scope` to UiSlice (replace, not merge leftovers). `GET /slice` refetch drives table, KPIs, chart, chips.
- Remove `sliceFromText` from the happy path. BUY_QUERY is `send(text)` only; `mode === "list"` sets `buyOnly`.
- 404 → “No encontré «X» en el catálogo.” Other chat/slice failures → “No pude cargar el catálogo. Intentá de nuevo en un momento.” Badge **Sin catálogo**. Never “motor caído”.
- Delete product demo catalog: `CATALOG`, `ROWS`, `compute()`, `answerFor()`, `useMock`, `VITE_SUPPLYMATE_USE_MOCK`, **Catálogo demo**.
- Round-trip `out_of_stock_only`, `name_tokens`, `subcategories` so slice matches Python.
- Open existing SKU drawer when `product_id` / `highlight_product_id` is present.

### Out of Scope
New chrome (evidence, guidance strip, extra KPIs), `/analyze`, splitting `index.tsx`, auth, Streamlit, raising table limit 50, archiving `explore-next-step-chips`.

## Capabilities

### New Capabilities
- `chat-scope-apply`: Map chat success/failure onto UiSlice + operator copy. No local NLP.

### Modified Capabilities
- `react-adapter`: Live catalog only. No demo fallback. Chat applies scope. Empty/error copy as above.

## Approach

Extract a pure mapper (`applyChatScope` + `scopePayloadToUiSlice` replace). `send()` posts current chrome scope, then replaces UiSlice from `res.scope`. `useSlice` never flips to mock rows.

## Affected Areas

- `frontend/src/lib/scope.ts`, `api.ts`, `data-source.ts`, `applyChatScope.ts` (new)
- `frontend/src/hooks/use-slice.ts`, `use-scope.ts`
- `frontend/src/routes/index.tsx`, `frontend/src/lib/supplymate.ts`
- Vitest: scope, applyChatScope, data-source; nextStepChips fixtures without `CATALOG`

## Risks

- `scope` null on single-SKU (Med): keep current recorte; open drawer from `product_id`.
- Replace vs refine (Med): Python sends the full `AnalyticalScope`; empty lists clear filters.
- Race open SKU vs slice refetch (Low): prefer `res.purchase_list` then live rows.

## Rollback Plan

Revert the branch. Demo catalog does not return.

## Success Criteria

- [ ] Chat “quiebre” updates Riesgo + live table/chart from `/data`.
- [ ] No `sliceFromText` / `ROWS` / `answerFor` on the product path.
- [ ] Unknown product and load failure use the operator copy; zero demo SKUs.
