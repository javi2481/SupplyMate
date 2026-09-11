# Tasks: Combinatorial recorte evals

Strict TDD per `openspec/config.yaml` (`strict_tdd: true`). Every implementation task is either a
**RED** task (write a failing test first) or a **GREEN** task (make the named RED task pass), plus
**TRIANGULATE** / **REFACTOR** where the design calls for it. Pure file moves and index edits are
marked **CHORE** and carry no test.

Conventions used below:

- CI set = `pytest -m "not performance and not llm"` (must stay green and Groq-free).
- Frontend set = `cd frontend && npm run test` (Vitest) and `npm run build` / `tsc`.
- No task may introduce a literal category, subcategory, supplier, SKU id, or answer phrase outside
  `tests/golden/traps/`.
- After any edit under `app/` or `frontend/src/`, `graphify update .` is run once at verify time
  (task 10.6), not per task.

---

## Phase 0 — SDD artifacts (complete)

- [x] 0.1 `proposal.md` — intent, scope, affected areas, assumptions, residual decisions, risks, rollback
- [x] 0.2 `design.md` — harness architecture, catalog-driven generation, oracle surfaces, three product fixes, cleanup plan, test layout, alternatives
- [x] 0.3 `specs/recorte-oracle/spec.md` — new capability delta (generation, pairwise budget, Python-only oracle, family policy, empty recorte, panel surface, horizon, refinement, unresolved, traps, drift, CI)
- [x] 0.4 `specs/llm-evals/spec.md` — promoted capability delta (paraphrase-only model, opt-in gating, shared expectations, frozen goldens)
- [x] 0.5 `specs/react-adapter/spec.md` — payload-shape panel rules plus the modified Unidades KPI requirement
- [x] 0.6 `tasks.md` — this file

---

## Phase 1 — Cleanup that unblocks clarity (archive + stale copy)

Runs first so `openspec/changes/` holds only this change while the harness is built, and so the
promoted specs are the ones the oracle is read against.

- [x] 1.1 CHORE — Record the archive precondition. Run the CI set and the frontend set on a clean tree and note pass counts plus the specific test modules that cover next-step chips and chat-scope apply (`tests/integration/guidance/test_guidance_plan.py`, `tests/unit/scope/`, `frontend/src/lib/applySuggestedFilter.test.ts`, `frontend/src/lib/applyChatScope.test.ts`, `frontend/src/lib/chatTurn.test.ts`). Confirm `explore-next-step-chips` is 17/17 and `wire-chat-scope` is 11/11 checked. Do not proceed to 1.2 if either set is red.
- [x] 1.2 CHORE — `git mv openspec/changes/explore-next-step-chips openspec/changes/archive/2026-09-11-explore-next-step-chips` and add `archive-report.md` in the `archive/2026-09-10-semantic-correctness/archive-report.md` shape, naming the green tests from 1.1 that cover the behaviour.
- [x] 1.3 CHORE — `git mv openspec/changes/wire-chat-scope openspec/changes/archive/2026-09-11-wire-chat-scope` and add its `archive-report.md` the same way.
- [x] 1.4 CHORE — Promote `archive/2026-09-11-explore-next-step-chips/specs/suggested-filters/spec.md` to `openspec/specs/suggested-filters/spec.md` as a new capability (deltas flattened into plain requirements).
- [x] 1.5 CHORE — Promote `archive/2026-09-11-wire-chat-scope/specs/chat-scope-apply/spec.md` to `openspec/specs/chat-scope-apply/spec.md` as a new capability.
- [x] 1.6 CHORE — Merge both archived `react-adapter` deltas by hand into the existing `openspec/specs/react-adapter/spec.md`. Read the promoted file once against both source deltas. This change's own `react-adapter` delta stays in `openspec/changes/` and MUST NOT be promoted here.
- [x] 1.7 CHORE — `git mv docs/operations/qa-consulta-desodorantes-2026-09-10.md` and `docs/operations/estado-superficies-2026-09-10.md` into `docs/operations/archive/`, and delete their two rows from the `docs/README.md` operations index (the dated snapshots become history, not navigation).
- [x] 1.8 CHORE — Drop stale Streamlit copy: remove the `| Streamlit | |` surface row from `docs/templates/change-request-template.md` and reword the header comment of `frontend/src/lib/scope-label.ts` so the policy statement stands without the retired-surface contrast.
- [x] 1.9 CHORE — Verify the cleanup criterion with a search that excludes `.venv/`, `node_modules/`, `__pycache__/` and `graphify-out/` (an unfiltered scan returns ~6000 hits from the vendored `streamlit` package in `.venv` and is useless). After 1.2, 1.3, 1.7 and 1.8 the only permitted remaining hits are: the guard line in `openspec/config.yaml`, everything under `openspec/changes/archive/` (which now includes both archived changes and both dated QA notes), and this change's own `proposal.md` / `design.md`, which describe the removal and move to `archive/` when this change is archived. Any other hit is a miss — record the exact command and its output in the verify notes.

---

## Phase 2 — Harness scaffolding: catalog axes and pairwise contracts

- [ ] 2.1 RED — `tests/evals/recorte/test_contract_generation.py`: generating twice with the fixed seed yields the same ordered contract set; every pair of axis values appears in at least one contract; the set is at or under `MAX_CONTRACTS`; if pair coverage needs more rows than the cap the generator raises instead of dropping pairs; a static scan of `axes.py` and `contracts.py` finds no literal category / subcategory / supplier / SKU string. Fails: modules do not exist.
- [ ] 2.2 GREEN — `tests/evals/recorte/__init__.py` and `tests/evals/recorte/conftest.py`: session-scoped `CatalogStore` fixture reused by every contract, plus the `--recorte-seed` option local to this directory (never passed by CI).
- [ ] 2.3 GREEN — `tests/evals/recorte/axes.py`: enumerate the seven axes from `get_store().products` at test time — `taxonomy` (category / subcategory with ≥2 SKUs), `supplier`, `risk` (`metrics.BUCKET_*` + `dashboard.COVERAGE_ORDER`), `name_token` (tokens in ≥2 product names), `horizon` (`{none, 15, 30}`), `relation` (`{new_query, refinement}`), `route_family` (`{purchase, sales, unresolved}`). Queries are shape-based ("a category with at least two subcategories"), never a named rubro.
- [ ] 2.4 GREEN — `tests/evals/recorte/contracts.py`: the `Contract{axes, expectations}` model, module-level `SEED` and `MAX_CONTRACTS = 200`, greedy IPOG-style 2-wise selection over a `random.Random(SEED)`-shuffled candidate list, and a stable parametrize `id` derived from the axis tuple so a failure names the combination. Makes 2.1 green.
- [ ] 2.5 CHORE — Register the `combinatorial_full` marker in `pyproject.toml` alongside `performance` and `llm`, and expose the full-cartesian path behind it. The CI expression `-m "not performance and not llm"` is unchanged and the full set is deselected by default.
- [ ] 2.6 RED — `tests/evals/recorte/test_catalog_drift.py`: assert the live store matches `catalog_shape.json` (counts of categories, subcategories, suppliers, total SKUs bucketed to the nearest 10 %, plus canonical coverage and health bucket names) and that the failure message names the drifted dimension and the refresh step. The snapshot MUST NOT hold per-node counts or node labels used as expectations. Fails: snapshot file missing.
- [ ] 2.7 GREEN — Generate `tests/evals/recorte/catalog_shape.json` from the live store and implement the actionable drift message. Makes 2.6 green.

---

## Phase 3 — Oracle predicates over the real pipeline

- [ ] 3.1 RED — `tests/evals/recorte/test_resolution_contracts.py`: parametrized over every contract at `resolution` depth, asserting `ResolvedReference.match_kind` and `scope_dimension`, the containment relation (a taxonomy resolution's `sku_ids` is a superset of the raw name hits for the same token), dimension exclusivity on `AnalyticalScope`, the `horizon_days` echo, refinement retention versus `new_query` reset (including `promote_new_query_if_needed`), and `blocking` plus non-empty `disambiguation_options` for unresolved refs. Fails: `oracle.py` and `pipeline.py` do not exist.
- [ ] 3.2 GREEN — `tests/evals/recorte/pipeline.py`: thin call-throughs at `resolution` depth (`interpret_query_rules` → `resolve_references` → `build_resolution_result`) reusing the session store.
- [ ] 3.3 GREEN — `tests/evals/recorte/oracle.py` part 1: the `ResolvedReference` and `AnalyticalScope` predicates from design §3. `recommended_quantity` is checked only for sign and consistency with `sku_count`; qty math stays in `tests/unit/replenishment/`. Makes 3.1 collectible and green except for the contracts that expose bug (a).
- [ ] 3.4 RED — `tests/evals/recorte/test_turn_contracts.py`: `turn` depth via `run_supplymate(message, scope=previous)`, asserting `dashboard.skus` equals the rows `dashboard.filter_rows` kept, the emptiness equivalence `purchase_list == [] ⇔ dashboard.purchase_skus == 0 ⇔ dashboard.recommended_units == 0`, absence of `ACTION_DRAFT_OC` in `suggested_filters` and of `guidance.action == "draft_oc"` on an empty slice, `mode` matching `route_family`, surface coherence (`dashboard is not None ⇒ scope is not None` and `scope` is the one the dashboard was computed from), the `horizon_days` echo, and `interpretation.disambiguation_options` non-empty exactly when `mode == "disambiguation"`.
- [ ] 3.5 GREEN — `tests/evals/recorte/oracle.py` part 2: the `ReplenishmentSlice` and `ChatResponse` predicates, including the structural numeric-claim probe (a regex over `\d+\s*(unidades|SKUs)` restricted to the "a reponer" phrasing). No predicate compares the answer to a stored sentence. Extend `pipeline.py` with the `turn` depth.
- [ ] 3.6 CHORE — Record the RED inventory: run the two contract modules and write down which failing contracts map to bug (a) resolution, bug (b) empty recorte, bug (c) panel surface. This list is the RED evidence table rows for phases 5–7 and the definition of done for each.

---

## Phase 4 — Trap goldens for known regressions

- [x] 4.1 RED — `tests/golden/traps/traps.csv` as a standalone commit (so the diff shows exactly which strings are frozen and why), columns `name, message, previous_scope, surface, assertion, issue`, with the three seen bugs: unresolved supplier token, an exact size token that must not match a longer size token, and family-over-name-hit resolution.
- [x] 4.2 RED — `tests/golden/traps/test_traps.py`: load the CSV and assert **only** oracle predicates (resolved dimension and set relation). No trap compares answer text to a stored sentence. Fails on the family trap until phase 5.
- [x] 4.3 RED → GREEN — Add the frozen-goldens guard: a test asserting the row counts of the four existing golden CSVs (`intents` 35, `multiturn` 4, `query_interpretation` 10, `reference_resolution` 16 including headers, read from the files at task time) are unchanged, with a message pointing new cases at `tests/golden/traps/` or a generated contract.

---

## Phase 5 — Bug (a): a matching taxonomy family beats a tiny name-hit set

- [x] 5.1 RED — Extend `tests/integration/reference_resolution/test_reference_resolver.py`: a token whose name hits all live under one taxonomy node whose label matches the token MUST resolve to that node (`scope_dimension` is `category` or `subcategory`, not `sku_set`) with `sku_count >= len(name_hits)`, and the resolved ref MUST keep the token in `name_tokens`. Case selected from the live store by shape, not by name.
- [x] 5.2 GREEN — `app/pipeline/reference_resolver.py`: add `FAMILY_CONTAINMENT` next to `MIN_GROUP_SCORE` and a `_family_from_name_hits(token, name_hits)` helper beside `_group_from_name_hits`, reusing the indexes from `_collect_entity_indexes`. Call it from the `len(name_hits) >= 2` branch of `resolve_single_reference` (subcategory first, then category), returning `sku_set` only when hits spread over ≥2 nodes at both levels.
- [x] 5.3 GREEN — Wire the same helper into the name-hit fallthrough of `_resolve_conjunction` so multi-token references get the identical policy.
- [x] 5.4 TRIANGULATE — Prove the other direction: a token matching names across more than one taxonomy node and matching no node label still resolves to `sku_set` with the token in `name_tokens`; the size-token trap from 4.1 stays green. Phase 3's containment assertion now passes for every name-token contract.
- [x] 5.5 CHORE — Regression net: `tests/golden/reference_resolution/`, `tests/regression/test_regressions.py` and `tests/integration/pipeline/` green with zero rows added to any golden CSV.

---

## Phase 6 — Bug (b): an empty recorte claims nothing and offers no OC

- [x] 6.1 RED — Extend `tests/unit/agent/test_explore_answer.py`: on an empty slice the answer contains the nothing-to-replenish statement and no unit / SKU-to-buy claim (asserted with the structural probe, not a phrase), `group_summaries` totals are never rendered as a purchase claim, and `dashboard.purchase_skus` may only be read as "how many more are in the panel". On a non-empty slice the claimed SKU count equals `dashboard.purchase_skus` and the claimed unit total equals `dashboard.recommended_units`.
- [x] 6.2 RED — Extend `tests/integration/guidance/test_guidance_plan.py`: an empty slice reaching the mission-complement branch MUST NOT return `action == "draft_oc"` nor quote `preview_union` units, and no `GuidanceChip` with action `draft_oc` is emitted.
- [x] 6.3 GREEN — `app/guidance/engine.py`: move the empty-purchase check above the mission-complement branch in `pick_next_question` as an early return on a condition false for every non-empty slice, and add the defensive non-empty assertion inside `_draft_oc_decision`. Offer a recorte-widening next step instead.
- [x] 6.4 GREEN — `app/agent/explore_answer.py`: collapse to a single `has_purchase = bool(slice_data.purchase_list)` gate and derive every unit / SKU claim from `slice_data.purchase_list` plus dashboard fields that are zero when the list is empty.
- [x] 6.5 GREEN — `app/agent/runner.py`: build the `ReplenishmentSlice` once per turn and pass it to guidance. `guidance_for_resolution` keeps its current signature for scope-only callers but gains a slice-accepting path, so the explore route never computes a second slice at `limit=25`. Routing branches untouched.
- [x] 6.6 TRIANGULATE — Pin `app/services/scoping/suggested_filters.py`: `ACTION_DRAFT_OC` stays gated on `recorte_qty > 0` and the oracle asserts it, so the gate cannot regress. Confirm non-empty copy is byte-identical to before the reorder via `tests/integration/agent/test_agent.py` and `tests/acceptance/`.

---

## Phase 7 — Bug (c): every mode carries its own panel surface

- [x] 7.1 RED — New `tests/unit/agent/test_top_categories_surface.py`: the sales turn returns `mode == "sales"`, a `dashboard` with its own bars, and a present `scope` describing the recorte it computed; and no `ChatResponse` from any mode carries a `dashboard` without a `scope`.
- [x] 7.2 GREEN — `app/agent/runner.py` `_run_top_categories`: return `scope=AnalyticalScope()` explicitly so the payload states the recorte it computed over instead of implying "nothing changed". Stated for all modes, so a future mode inherits the rule.
- [x] 7.3 RED — Extend `frontend/src/lib/applyChatScope.test.ts` with the payload-shape pairs, using hand-written `ChatResponse` fixtures (no catalog reads): `scope` present maps the recorte as today; `scope` absent with a `dashboard` replaces the live panel with that surface and leaves no previous category, health, coverage or context-bar filter behind (the sales reset case); `scope` and `dashboard` both absent leaves the slice untouched; the `mode === "list"` `buyOnly` toggle still applies. No branch keys on a mode string other than that toggle.
- [x] 7.4 GREEN — `frontend/src/lib/applyChatScope.ts`: decide on the pair, not the mode — replace from `res.scope` when present, replace with the root recorte when `scope` is null but `dashboard` is present, keep `current` when neither is present. `buyOnly` for `mode === "list"` stays the one purchase-specific rule.
- [x] 7.5 GREEN — `frontend/src/routes/index.tsx`: stop deriving `chatBoard` independently from `res.dashboard` and consume the branch `applyChatScope` already decided, so chips, KPIs and chart come from one decision. Update `frontend/src/lib/chatTurn.test.ts` expectations if the single decision changes its recorded panel shape.
- [x] 7.6 RED → GREEN — Replaced-surface KPI rule from the `react-adapter` MODIFIED requirement: under a `scope`-less replaced surface the purchase KPI row (`Unidades a pedir`, SKUs to replenish, estimated purchase value) MUST NOT render at all and the stale `recommended_units` MUST NOT appear anywhere; recorte purchase actions (CSV export, build the order) MUST NOT be offered for the prior slice. Test first in the KPI/panel component test, then the component change.
- [x] 7.7 RED → GREEN — Two-turn continuity contract: recorte in force → sales-ranking turn → follow-up classified `refinement` yields the pre-existing recorte plus the new filter, never the whole catalog. Eval harness `tests/evals/recorte/test_turn_contracts.py` is not built yet (Phase 3), so the stand-in is `tests/integration/agent/test_sales_refinement_continuity.py` plus the `conversationSlice` assertions in `applyChatScope.test.ts`. Confirms the replacement is local to the panel and was not sent to the server as a filter change.

---

## Phase 8 — Gated paraphrase sampling (the model never judges)

- [ ] 8.1 RED — `tests/evals/recorte/test_llm_paraphrase.py`: marked `@pytest.mark.llm`, skips unless `RUN_LLM_EVALS=1`, and a missing key is a skip rather than a failure. Assert the module is fully deselected under the CI expression and that the default run issues zero outbound model requests.
- [ ] 8.2 GREEN — `tests/evals/recorte/llm_paraphrase.py`: sample a subset of generated contracts, ask the model for an alternative phrasing of the question only, feed the phrasing through the same `pipeline.py` depth, and assert with the **identical** expectation object from the contract. No relaxed expectation set, no second prose-based expectation.
- [ ] 8.3 CHORE — No-judge guard: a default-marker test that inspects model call sites in `tests/` and asserts every one is classification or paraphrase generation — none receives an assistant answer as input or returns a score, grade or verdict used in an assertion.
- [ ] 8.4 CHORE — Document the triage loop in the eval module docstring: a paraphrase failure is reported as the broken invariant plus the axis combination, and is captured as a deterministic trap under `tests/golden/traps/` so it reproduces without a model.

---

## Phase 9 — Docs and the eval contract

- [x] 9.1 CHORE — `docs/contract/evaluation.md`: add the oracle section (two entry depths, catalog-driven axes, pairwise + seed + cap, `combinatorial_full` opt-in, drift snapshot, traps directory), restate the no-judge rule (Groq paraphrases inputs; Python scores), and declare the four golden CSVs frozen in row count.
- [x] 9.2 CHORE — Mirror the same section in `docs/contract/evaluation.es.md`, keeping the bilingual pair in sync.
- [ ] 9.3 CHORE — `docs/README.md`: confirm the two dated rows removed in 1.7 are gone and no index row implies Streamlit is a live surface.

---

## Phase 10 — Verify

- [ ] 10.1 Run the CI set `pytest -m "not performance and not llm"` with no Groq key present: green, contracts and traps executed, zero outbound model requests.
- [ ] 10.2 Run the frontend set: `npm run test` (Vitest, including `applyChatScope.test.ts` and `chatTurn.test.ts`) and a clean type-check / build.
- [ ] 10.3 Run `pytest -m performance` as the runtime backstop and compare against `docs/operations/performance-profile.md` thresholds; if the added contract runtime breaks the budget, move the offending set behind `performance` or `combinatorial_full` rather than trimming pair coverage.
- [ ] 10.4 Run the opt-in sets once: `pytest -m combinatorial_full` (full cartesian smoke) and, if a key is available, `RUN_LLM_EVALS=1 pytest -m llm`. Record the outcome, or record the skip reason if no key.
- [ ] 10.5 Run `ruff check .` and the coverage gate (`fail_under = 85` over the included `app/` modules, which now include the edited `reference_resolver.py` and `engine.py`).
- [ ] 10.6 Run `graphify update .` so the graph reflects the resolver, guidance, runner and frontend edits.
- [ ] 10.7 Write `openspec/changes/combinatorial-recorte-evals/verify-report.md` with the TDD evidence table (one row per RED task: failing assertion before, passing after), the commands and results from 10.1–10.6, the golden CSV row counts before and after, and the proposal's success-criteria checklist ticked with evidence.
