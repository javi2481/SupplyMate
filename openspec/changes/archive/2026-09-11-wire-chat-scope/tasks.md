# Tasks: Wire chat scope

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 350–450 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |

## Phase 1: Vitest RED

- [x] 1.1 `scope.test.ts`: replace semantics (empty cats clear prior category); `out_of_stock_only` / `name_tokens` / `subcategories` round-trip.
- [x] 1.2 Create failing `applyChatScope.test.ts`: quiebre scope → riesgo_quiebre; mode list → buyOnly; 404 / load-fail copy; null scope keeps slice.
- [x] 1.3 `data-source.test.ts`: `Sin catálogo` not `Catálogo demo`; `preferLiveApi` ignores mock flag; no `ROWS` fallback test.

## Phase 2: Vitest GREEN (mappers)

- [x] 2.1 `scope.ts` replace + extra fields; `api.ts` payload/`HttpError`.
- [x] 2.2 `applyChatScope.ts` + `data-source.ts` labels/copy.
- [x] 2.3 Vitest on those files green.

## Phase 3: Product path

- [x] 3.1 `use-slice.ts`: drop `useMock`; empty on error.
- [x] 3.2 `index.tsx`: `useScope` / UiSlice; `send()` applies mapper; no `sliceFromText` / `answerFor` / `ROWS`; chips live-only; export API-only; chart error copy.
- [x] 3.3 Delete `CATALOG`/`ROWS`/`compute`/`answerFor`; `.env.example` / README; nextStepChips tests without catalog.

## Phase 4: Verify

- [x] 4.1 `npx vitest run` in `frontend` green.
- [x] 4.2 `graphify update .`
