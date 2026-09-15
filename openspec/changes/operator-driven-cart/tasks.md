# Tasks: Operator-driven cart (row add)

Strict TDD. Frontend: `cd frontend && npx vitest run <file>`.

## Phase 1 — Helpers

- [x] 1.1 SDD updated (row add + export finish)
- [x] 1.2 RED/GREEN `addLineToCart` empty/0 no-op; add; upsert

## Phase 2 — UI

- [x] 2.1 SkuTable: hide Cobertura/Prioridad; empty A pedir + sug; cart; Tab/Enter
- [x] 2.2 Remove global CTA; wire addLine + footer
- [x] 2.3 Exportar y terminar

## Phase 3 — Verify

- [x] 3.1 Vitest green
- [x] 3.2 `graphify update .`

Note: Tab keyboard order is verified manually (no RTL in frontend).
