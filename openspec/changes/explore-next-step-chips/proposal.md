# Proposal: Explore next-step chips

## Intent

Explore prompt chips are hardcoded (`DEFAULT_CHIPS`: SKU 6033436, first category, “Sobrestock”). They ignore the recorte and `send(label)` as chat. Next steps MUST come from `suggest_next_filters` (on `GET /replenishment/slice` as `suggested_filters`). Frozen chrome except this strip.

## Scope

### In Scope
- Cap `suggest_next_filters` 3 → 6; skip active filters; no LLM; values from snap/items.
- Extra candidates: 2nd `by_category`, overstock health, `draft_oc`.
- Short question-style labels (not “Ver X — N SKUs · u.”).
- Explore: ≤6 chips in a 3×2 grid from `suggested_filters`; fewer if fewer; hide if empty; never pad.
- Click applies the action on UiSlice / SKU drawer / PO (`filter_*`, `open_sku`, `draft_oc`). MUST NOT `send(label)`.
- Catálogo demo: equivalent chips from mock rows and existing mock qty; no second replenishment formula.

### Out of Scope
Chrome redesign, splitting `index.tsx`, auth, Streamlit UI, raising table limit, LLM-invented questions/quantities.

## Capabilities

> Not in `openspec/specs/` (only unarchived `ui-v2` / `interactive-drilldown` deltas). Treat as **new**.

### New Capabilities
- `suggested-filters`: Deterministic chips from slice data. Cap 6, skip active, short question labels, extra types (2nd category, overstock, `draft_oc`), no LLM.

### Modified Capabilities
- `react-adapter`: Explore prompt chips consume `suggested_filters` (mock equivalent offline), 3×2 grid, apply action not send text.

## Approach

Python decides; UI presents. Extend `suggested_filters.py`. Surface `suggested_filters` from `useSlice` (fetched today, dropped). Apply via `pushSlice` / SKU drawer / `openPo()`. Mock uses the same order on existing rows.

Order (first applicable, cap 6): top category → coverage (`0–3 días` else next populated) → stockout_risk → top supplier → top SKU `open_sku` → 2nd category → overstock → `draft_oc`.

## Affected Areas

- `app/services/scoping/suggested_filters.py` + unit tests — cap 6, extra candidates, short labels, `draft_oc`
- `frontend/src/hooks/use-slice.ts` — expose `suggested_filters`
- `frontend/src/routes/index.tsx` — replace `DEFAULT_CHIPS`; 3×2; apply actions
- `frontend/src/lib/scope.ts` — `filter_supplier` on UiSlice / query
- Mock chip helper — rank from mock rows

## Risks

- Live vs mock drift (Med): same order; mock uses existing qty.
- `open_sku` off the table page (Med): open from purchase_list/mock row; keep limit 50.
- UiSlice has no `supplier` (Med): add to slice query (`slice-api` already lists it).
- Short labels also hit Streamlit (Low): side effect; Streamlit out of scope.

## Rollback Plan

Revert the branch. Payload stays `{action, args, label}`. Frontend can hide the strip or restore `DEFAULT_CHIPS`.

## Dependencies

Existing slice `suggested_filters` / `SuggestedFilter`; Explore `openPo()` and SKU drawer.

## Success Criteria

- [ ] Live chips from `suggest_next_filters` (≤6, skip active, no padding, hide if empty).
- [ ] Click applies action; chat does not receive the chip label.
- [ ] Short question labels; no LLM; mock chips from mock rows; 3×2; chrome unchanged.
