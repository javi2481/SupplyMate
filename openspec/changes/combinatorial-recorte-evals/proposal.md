# Proposal: Combinatorial recorte evals

## Intent

Manual QA cannot cover axis combinations (taxonomy × supplier × coverage/health × horizon × follow-up × sales-vs-purchase × unresolved). The failures found in QA tanda 5 are **recorte and surface invariants**, not prose quality: `toallitas` resolves to a tiny name-hit `sku_set` instead of the real family; an empty purchase still narrates "N SKUs a reponer" and offers `draft_oc`; a `sales_categories` turn leaves the Explore panel showing the previous full-catalog replenishment KPIs and chart. We need a Python oracle over generated combinations, plus cleanup of dead weight that makes the harness confusing to build on.

## Scope

### In Scope
- `recorte-oracle`: contracts generated from `CatalogStore` (axis combinations, never hardcoded rubros) asserted by Python over `resolve_references → build_scope → replenishment_slice → ChatResponse`.
- Recorte invariants as assertions: family-over-name-hit resolution, empty-recorte answer/guidance integrity, panel-surface continuity per `mode`, horizon echo, follow-up scope retention, unresolved → disambiguation.
- RED tests then fixes for the three QA tanda 5 bugs (a: resolver family policy, b: empty purchase copy + no `draft_oc`, c: sales mode must replace the Explore panel surface).
- Gated LLM paraphrase sampling of **contracts** (`RUN_LLM_EVALS=1`, `-m llm`); CI stays `pytest -m "not performance and not llm"`.
- Cleanup (see Affected Areas): archive two shipped changes, archive dated QA notes, remove stale Streamlit copy, freeze golden CSV growth.

### Out of Scope
LLM-as-judge of chat quality; new agents or pipeline stages; changing qty math; frontend chrome beyond the panel reset; raising CI to live Groq; rewriting the 4 existing golden CSVs.

## Capabilities

### New Capabilities
- `recorte-oracle`: catalog-driven combinatorial contracts + Python assertions on `ResolvedReference` / `AnalyticalScope` / `ReplenishmentSlice` / `ChatResponse`, including the family-resolution and empty-recorte invariants.
- `llm-evals`: promote the archived concept (`archive/2026-09-10-semantic-correctness/specs/llm-evals`) and extend it: the LLM MAY paraphrase contracts; it MUST NOT judge answers.

### Modified Capabilities
- `react-adapter`: non-purchase modes (`sales`) MUST replace, not inherit, the panel surface when `ChatResponse.scope` is absent.

## Approach

A contract is `{axes, expectations}` built by enumerating live catalog values (one category, one subcategory, one supplier, one coverage/health bucket, a name token, plus horizon / follow-up / unresolved variants) — pairwise across axes with a fixed seed, so no rubro is frozen in a fixture. Each contract runs the real pipeline and asserts shape: which `scope_dimension` won, `sku_count` vs the containing taxonomy node, `mode`, whether the answer may claim units, whether `draft_oc` is allowed. Known bugs stay as a small `tests/golden/traps/` list (avon unresolved, `xxg` ≠ `xxxg`, `toallitas` family). Strict TDD per `openspec/config.yaml`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tests/evals/recorte/` | New | Contract generator, oracle, pairwise runner |
| `tests/golden/traps/` | New | Named regression cases for known bugs |
| `app/pipeline/reference_resolver.py` | Modified | Family-over-name-hit policy (`_group_from_name_hits`, `_pick_best_group`) |
| `app/agent/explore_answer.py`, `app/guidance/engine.py` | Modified | Empty recorte MUST NOT claim SKUs nor offer `draft_oc` |
| `app/agent/runner.py` (`_run_top_categories`) | Modified | `sales` must carry an explicit panel surface |
| `frontend/src/lib/applyChatScope.ts` | Modified | Reset/replace panel for non-purchase modes |
| `openspec/changes/{explore-next-step-chips,wire-chat-scope}` | Archived | Tasks 17/17 and 11/11 done and covered by green tests → move to `archive/2026-09-11-*`, promote their specs to `openspec/specs/` |
| `docs/operations/{qa-consulta-desodorantes,estado-superficies}-2026-09-10.md` | Archived | Move to `docs/operations/archive/`, trim `docs/README.md` index |
| `docs/templates/change-request-template.md`, `docs/README.md`, `frontend/src/lib/scope-label.ts` | Modified | Drop stale Streamlit rows/comments |
| `docs/contract/evaluation{,.es}.md` | Modified | Document the oracle + no-judge rule; declare golden CSVs frozen |

## Assumptions

Settled by the user; documented, not re-litigated:

1. Failures are recorte/surface invariants, not prose quality.
2. Python is the oracle; the LLM only paraphrases contracts. Groq is never a judge (Engram decision #944).
3. Policies act on recorte **shape**; no hardcoded category, SKU, or golden phrase. Small trap goldens for known bugs are allowed.
4. Cleanup is part of this change, not a follow-up.
5. QA tanda 5 bugs (a)(b)(c) are driven by RED tests here.
6. Architecture stays `interpret_query_llm → resolve_references → build_scope → replenishment_slice`; Python owns qty; no new agents.
7. CI has no live Groq; live paraphrase sampling is `RUN_LLM_EVALS=1` only.
8. Strict TDD.

### Residual open decisions (recommended defaults)

| Decision | Recommended default |
|----------|---------------------|
| Combinatorial budget: full cartesian vs sampled | **Pairwise (2-wise) with a fixed seed, capped ~200 contracts**, full cartesian only behind an opt-in `-m combinatorial_full` marker, so CI runtime stays inside the existing performance budget. |
| Contract source: committed snapshot vs runtime generation | **Generate from `CatalogStore` at test time** (keeps rubros unfrozen); commit only the `traps/` list plus a coarse shape/count snapshot to detect catalog drift. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Catalog CSV changes break generated contracts | Med | Assert shape relations (family ⊇ name hits), not absolute counts; coarse drift snapshot |
| Combinatorial runtime blows up CI | Med | Pairwise + cap; reuse one `CatalogStore`; full matrix opt-in only |
| Archiving a change that is not truly shipped | Low | Archive only when tasks are 100% checked **and** behavior is covered by green tests |
| Panel reset for `sales` regresses follow-up continuity | Med | Contract for `sales → follow-up` retains the prior recorte where the follow-up is a refinement |
| Paraphrase sampling becomes a de facto judge | Low | Spec states the LLM output feeds the same Python oracle; no scoring of prose |

## Rollback Plan

The harness is additive and test-only: delete `tests/evals/recorte/` and `tests/golden/traps/`. The three product fixes are isolated commits (resolver policy, empty-recorte copy/guidance, sales panel surface) and can be reverted individually. Archived changes and docs are moves recoverable with `git mv` in reverse; `openspec/specs/` promotions revert with the branch.

## Dependencies

- `graphify-out/graph.json` current (`graphify update .` after edits)
- Live catalog CSVs loaded by `CatalogStore` (no new data source)
- Optional for gated evals only: Groq key + `RUN_LLM_EVALS=1`

## Success Criteria

- [ ] Generated contracts cover all axes pairwise, with zero hardcoded category/SKU/golden phrase in the generator.
- [ ] The three QA tanda 5 bugs each have a RED test that fails before the fix and passes after.
- [ ] `pytest -m "not performance and not llm"` is green and no test requires Groq.
- [ ] `RUN_LLM_EVALS=1 pytest -m llm` paraphrases contracts and reuses the same Python oracle — no prose scoring anywhere.
- [ ] `openspec/changes/` contains only this change; the two shipped changes are archived and their specs promoted.
- [ ] No Streamlit reference remains outside `openspec/changes/archive/`; golden CSVs unchanged in row count.
