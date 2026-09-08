# Proposal: lovable-api-adapter

## Why

The Lovable React UI (Etapa A) is product-ready for navigation and copy, but
`frontend/src/lib/api.ts` only serializes a subset of `AnalyticalScope`, while
the UI still runs a local `compute()` mock engine. Declared TypeScript types
claim full scope; HTTP does not. Priority and coverage labels diverge from the
Python domain (`critical|high|normal`, `COVERAGE_ORDER`).

Operators need the frozen UX wired to FastAPI without redesigning the backend
and without inventing replenishment math in the browser.

## What Changes

- Complete `ScopeQuery` / `toSearchParams` parity with FastAPI `_scope_dependency`
- `scope.ts` + `adapter.ts`: UI recorte → query params; `PurchaseListItem` → visual row
- Align coverage chips to backend `COVERAGE_ORDER` (5 bands, en-dash labels)
- Priority labels 1:1 with `PRIORITY_LABELS` (Crítica / Alta / Normal)
- Vitest for scope serialization and adapter projection
- Etapa B: `useQuery(['slice', scope])`, `postChat`, SKU replenishment, CSV;
  mock catalog as offline fallback only

## Capabilities

- Modified: `slice-api` (TypeScript client serializes full AnalyticalScope query params)
- New: `react-adapter` (visual projection + scope mapping; no domain math when API is up)

## Non-Goals

- Auth, persisted threads/recortes, `POST /replenishment/analyze`
- Massive `index.tsx` split into 15 components
- Streamlit features; redesign FastAPI contracts
- Frontend order-up-to formula when API is available

## Rollback

Delete `openspec/changes/lovable-api-adapter/`, revert `frontend/src/lib/{api,scope,adapter,supplymate}.ts`,
hooks, Vitest config, and `index.tsx` wiring to the mock-only Etapa A snapshot.

## Risks

- Coverage band unicode (`–` vs `-`) must match `dashboard.COVERAGE_ORDER` exactly
- `sin_stock` is a client filter (stock === 0), not an API `health_bucket`
- Offline fallback must never show localhost / raw API URLs in product copy
