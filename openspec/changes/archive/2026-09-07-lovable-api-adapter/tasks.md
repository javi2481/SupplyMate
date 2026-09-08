# Tasks: lovable-api-adapter

## Phase 0 — SDD

- [x] 0.1 proposal.md, design.md, specs, tasks.md

## Phase 1 — Etapa A.5 (Strict TDD)

- [x] 1.1 Add Vitest; RED tests for `scope` serialization + `adapter` projection
- [x] 1.2 GREEN: complete `ScopeQuery` / `toSearchParams`; add `scope.ts` + `adapter.ts`
- [x] 1.3 Align coverage chips to 5 `COVERAGE_ORDER` bands; priority `critical|high|normal`
- [x] 1.4 RED/GREEN Python contract: `coverage_bucket=0–3 días` filters slice

## Phase 2 — Freeze

- [x] 2.1 Confirm UX freeze (no Lovable shell redesign) before Etapa B

## Phase 3 — Etapa B (Strict TDD)

- [x] 3.1 RED tests: `fetchSlice` query string, 404/422, offline fallback without URL leak
- [x] 3.2 GREEN: `useSlice` / `useScope` + `useQuery(['slice', scope])`
- [x] 3.3 Wire `postChat`, SKU replenishment drawer, CSV URL; `compute()` mock-only fallback
- [x] 3.4 Product copy: Motor listo / Catálogo demo; no API/slice/understock chrome

## Phase 4 — Verify

- [x] 4.1 `npm test` (frontend) + `pytest tests/contract/api_contract/`
- [x] 4.2 Manual: coverage → category → risk → SKU → PO → export with API on :8000
- [x] 4.3 `graphify update .`

## Deferred (do not archive until decided)

- [x] 5.1 Replace 4 Lovable coverage chips (`0-3|3-7|7-14|14+`) with 5 `COVERAGE_ORDER` bands (`14+` today maps to `14–30 días` + `30+ días`)
