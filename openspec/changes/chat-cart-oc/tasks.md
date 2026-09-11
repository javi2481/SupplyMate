# Tasks: Chat cart → OC

Strict TDD (`openspec/config.yaml`). Frontend set: `cd frontend && npx vitest run <file>`.

Review Workload Forecast:
- Decision needed before apply: No
- Chained PRs recommended: No
- 400-line budget risk: Medium
- Delivery: single apply batch (parent assigned Block B)

## Phase 1 — Pure cart merge (TDD)

- [x] 1.1 RED/GREEN `emptyCart` / `cartTotals`
- [x] 1.2 RED/GREEN `mergeCart` new_query max-by-product_id (never sum)
- [x] 1.3 RED/GREEN `mergeCart` refinement drops shared category then adds
- [x] 1.4 RED/GREEN sales / empty purchase_list / non-purchase mode no-op

## Phase 2 — Thread persistence

- [x] 2.1 ThreadPanel/ThreadState `cart`; emptyPanel/panelOf/panelAfterChat preserve or default empty
- [x] 2.2 New thread / delete last → empty cart; switchThread restores cart
- [x] 2.3 `send()` merges purchase into thread cart after success

## Phase 3 — OC, CSV, footer

- [x] 3.1 `resolvePoRows`: cart if non-empty else focus purchase list
- [x] 3.2 Client CSV text from cart
- [x] 3.3 Footer `En el pedido: N líneas · X u.`
- [x] 3.4 Wire `index.tsx` openPo / export / footer; OC allowed when cart non-empty even on replaced surface

## Phase 4 — Verify

- [x] 4.1 Vitest green for touched files
- [x] 4.2 `graphify update .`

---

## Block C (light) — traps, frozen goldens, cart scenario eval note

Applied in a separate batch (MVP eval harness):

- [x] C.1 `tests/golden/traps/traps.csv` + `test_traps.py` (oracle predicates only)
- [x] C.2 `tests/golden/test_frozen_golden_counts.py` (intents 35, multiturn 4, query_interpretation 10, reference_resolution 16)
- [x] C.3 Vitest multi-turn cart scenario in `frontend/src/lib/cart.test.ts`
- [x] C.4 `docs/contract/evaluation.md` + `.es.md` (oracle/traps/cart, frozen goldens, no LLM judge)
