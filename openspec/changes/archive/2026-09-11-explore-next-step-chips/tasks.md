# Tasks: Explore next-step chips

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 280–360 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Ranker + Explore chips | PR 1 | `pytest tests/unit/dashboard/test_suggested_filters.py` then `npx vitest run src/lib/scope.test.ts src/lib/nextStepChips.test.ts src/lib/applySuggestedFilter.test.ts` (cwd `frontend`) | Explore + FastAPI: ≤6 chips, hide empty, click filter/`open_sku`/`draft_oc`, chat unchanged; Catálogo demo same | Revert branch; payload `{action,args,label}` unchanged |

Follow **spec ranking** (Cap scenario), not the design table: unused cat0 → unused cat1 → coverage (`0–3 días` else next populated) → stockout → overstock → unused supplier → `open_sku` → `draft_oc`.

## Phase 1: Pytest RED

- [x] 1.1 `tests/unit/dashboard/test_suggested_filters.py`: failing Sparse (len=2, no pad) and Overflow (first six spec slots; drop `open_sku`/`draft_oc`).
- [x] 1.2 Failing skip-active: omit `filter_*` already in `AnalyticalScope`; still consider `open_sku`/`draft_oc`.
- [x] 1.3 Failing Cap (A, B, coverage, stockout_risk, overstock, supplier) and Draft OC only (one `draft_oc`).
- [x] 1.4 Failing labels/payload: `¿Qué hay en Cuidado?` not `Ver …`; overstock `filter_health` + `health_bucket=overstock`; `draft_oc` args `{}`.

## Phase 2: Pytest GREEN

- [x] 2.1 `app/services/scoping/suggested_filters.py`: cap 6; spec rank; skip active; short labels; `ACTION_DRAFT_OC`; no LLM/`Runner`.
- [x] 2.2 `ui/streamlit_app.py` `apply_filter_action`: `draft_oc` → `_enter_commit_mode()`; leave `compose_next_step` cap 3.
- [x] 2.3 `pytest tests/unit/dashboard/test_suggested_filters.py` green.

## Phase 3: Vitest RED

- [x] 3.1 Fail `frontend/src/lib/scope.test.ts`: `UiSlice.suppliers` round-trips `sliceToScopeQuery` `supplier`.
- [x] 3.2 Create failing `frontend/src/lib/nextStepChips.test.ts`: spec rank/skip/cap/no-pad on fixture `Calc[]`; qty from mock `compute()`.
- [x] 3.3 Create failing `frontend/src/lib/applySuggestedFilter.test.ts`: union cats/suppliers/health; set coverage; `stockout_risk`→`riesgo_quiebre`, `overstock`→`sobrestock`; unknown no-op; never `send`.

## Phase 4: Vitest GREEN

- [x] 4.1 `frontend/src/lib/scope.ts`: `suppliers: string[]` on `UiSlice`; query/payload `supplier`.
- [x] 4.2 Create `frontend/src/lib/nextStepChips.ts` mock ranker (spec order, skip-active, cap 6).
- [x] 4.3 Create `frontend/src/lib/applySuggestedFilter.ts` command map (`open_sku`/`draft_oc` commands; unknown no-op).
- [x] 4.4 Vitest on those three files green.

## Phase 5: Wiring

- [x] 5.1 Export `SuggestedFilter` from `frontend/src/lib/api.ts`; `frontend/src/hooks/use-slice.ts` returns `suggestedFilters` from `fetchSlice`.
- [x] 5.2 `frontend/src/routes/index.tsx`: drop `DEFAULT_CHIPS`/chat chips; `Slice.suppliers`; Explore 3×2 after recorte; live=`suggestedFilters`, mock=`mockNextStepChips`; hide empty; never pad; do not split; do not migrate `useScope`.
- [x] 5.3 Wire click → `applySuggestedFilter` → `pushSlice`; `open_sku` via rows then purchaseList/`ROWS` then `openDetail` (limit 50); `draft_oc`→`openPo()`; never `send(label)`.
