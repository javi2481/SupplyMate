# Design: Combinatorial recorte evals

> `openspec/changes/combinatorial-recorte-evals/specs/` does not exist yet at the time of writing.
> This design derives from `proposal.md`; the spec deltas (`recorte-oracle`, `llm-evals`, `react-adapter`)
> land in parallel and MUST stay consistent with the invariants named here.

## 1. Technical approach

The eval harness is a **second reader of the existing pipeline**, not a new stage. It calls the same
functions the API calls, in the same order, and asserts on the dataclasses that already cross those
boundaries. Nothing in `app/` learns about the harness.

```
                     tests/evals/recorte/                          app/  (unchanged shape)
  CatalogStore ──► axes.py      (enumerate live values)
                      │
                      ▼
                   contracts.py (pairwise, seeded, cap ~200)
                      │  Contract{axes, expectations}
                      ▼
                   pipeline.py  ──► interpret_query_rules ──► app/pipeline/query_interpretation.py
                                    resolve_references    ──► app/pipeline/reference_resolver.py
                                    build_resolution_result ► app/pipeline/scope_builder.py
                                    replenishment_slice   ──► app/services/analytics/catalog_service.py
                                    run_supplymate        ──► app/agent/runner.py
                      │
                      ▼
                   oracle.py    (assert invariants on the 4 surfaces)
                      ▲
                      │  same oracle, different input text
                   llm_paraphrase.py  (marker `llm`, RUN_LLM_EVALS=1)
```

Two entry depths, because not every invariant needs a full turn:

| Depth | Entry point | Surfaces asserted | Cost |
|-------|-------------|-------------------|------|
| `resolution` | `resolve_references` + `build_resolution_result` | `ResolvedReference`, `AnalyticalScope` | cheap; most contracts |
| `turn` | `run_supplymate(message, scope=previous)` | + `ReplenishmentSlice`, `ChatResponse` | one slice per contract; the pairwise cap exists for this |

`tests/conftest.py` already pins the catalog to `data/` and stubs `interpret_query_llm` off, so the
default (non-`llm`) run is deterministic and Groq-free with no extra wiring.

## 2. Catalog-driven contract generation

### Axes

Every axis value is **read from `CatalogStore` at test time** (`get_store().products`), never written
into a file. No rubro, SKU or phrase is frozen in the generator.

| Axis | Values derived from | Notes |
|------|--------------------|-------|
| `taxonomy` | distinct `ProductMaster.category` / `.subcategory` with ≥2 SKUs | sampled, not exhaustive |
| `supplier` | distinct `ProductMaster.supplier` | one per contract |
| `risk` | `metrics.BUCKET_*` + `dashboard.COVERAGE_ORDER` | health and coverage buckets |
| `name_token` | tokens that appear in ≥2 product names **and** are contained by exactly one category | the family axis (see §4a) |
| `horizon` | `{none, 15, 30}` phrased in the message | asserted as an echo, not a qty |
| `relation` | `{new_query, refinement}` | refinement runs a two-turn contract |
| `route_family` | `{purchase, sales, unresolved}` | drives which surface invariants apply |

Nothing above names a rubro; the generator asks the store *"give me a category with at least two
subcategories"*, not *"give me Cosmetica"*.

### Pairwise, seed, cap

- Full cartesian of the seven axes is far beyond the CI budget, so the default set is **2-wise
  coverage**: every pair of axis values appears in at least one contract. A greedy IPOG-style
  selection over a `random.Random(SEED)`-shuffled candidate list gets ~2-wise coverage in well under
  200 rows for these axis cardinalities.
- `SEED` is a module constant so a failure is reproducible from the test id alone. `--recorte-seed`
  (a `conftest.py` option local to `tests/evals/recorte/`) allows a one-off different draw when
  hunting for new failures; CI never passes it.
- `MAX_CONTRACTS = 200` is a hard cap applied after pair coverage; if pair coverage needs more rows
  than the cap, the run fails loudly rather than silently dropping pairs.
- Full cartesian is available behind `-m combinatorial_full` (new marker in `pyproject.toml`,
  excluded from the CI expression exactly like `performance` and `llm`).

### Drift snapshot

Rubros are not frozen, but **catalog shape** is. `tests/evals/recorte/catalog_shape.json` holds
coarse counts (number of categories, subcategories, suppliers, total SKUs, bucketed to the nearest
10 %) and a test asserts the live store still matches. A CSV swap that changes the world therefore
fails one obvious test instead of scattering failures across 200 generated ones.

### Traps

`tests/golden/traps/traps.csv` is the only place where concrete strings live, and only for bugs we
have actually seen: `avon` (unresolved), `xxg` vs `xxxg` (size token confusion), `toallitas`
(family over name hits). Columns: `name, message, previous_scope, surface, assertion, issue`.
Committed as a **separate commit** from the generator so the diff shows which strings are frozen and
why. A trap row is a pointer at an invariant, not a golden phrase: it asserts the same oracle
predicates, never an exact answer string.

## 3. Oracle assertion surfaces

The oracle is a set of small predicates in `tests/evals/recorte/oracle.py`. Each reads one surface.

**`ResolvedReference`** (from `resolve_references`)
- `match_kind` ∈ the kind the contract expects (`group` / `exact_sku` / `unresolved` / `ambiguous`).
- `scope_dimension` is the expected dimension; in particular a token with name hits inside a single
  taxonomy node MUST NOT come back as `sku_set` (§4a).
- **Containment**, not counts: when `scope_dimension` is `category`/`subcategory`, `sku_ids` MUST be
  a superset of the raw name hits for the same token. This is the relation that survives a CSV edit.
- `recommended_quantity` is only checked for sign/consistency with `sku_count`; qty math belongs to
  `tests/unit/replenishment/`.

**`AnalyticalScope`** (from `build_scope` / `build_resolution_result`)
- The dimension that won in `ResolvedReference` is the dimension populated in the scope, and no
  other taxonomy dimension is populated by accident.
- `horizon_days` echoes the horizon the message asked for (`resolve_horizon_days`).
- For `relation == "refinement"`, the previous scope's values are retained and the new axis is added;
  for `new_query` (including the `promote_new_query_if_needed` promotion) the previous values are gone.
- Unresolved refs with no risk hints produce `blocking = True` and non-empty `disambiguation_options`.

**`ReplenishmentSlice`** (from `catalog_service.replenishment_slice`)
- `dashboard.skus` equals the number of rows `dashboard.filter_rows` kept for that scope — the panel
  and the recorte agree.
- Emptiness is **one fact**: `purchase_list == []` ⇔ `dashboard.purchase_skus == 0` ⇔
  `dashboard.recommended_units == 0`. Contracts assert the equivalence, not a number.
- `suggested_filters` MUST NOT contain `ACTION_DRAFT_OC` when the slice is empty.
- `guidance.action` ≠ `draft_oc` when `purchase_list` is empty.

**`ChatResponse`** (from `run_supplymate`)
- `mode` matches the contract's `route_family`.
- **Claim integrity**: if `purchase_list` is empty, `answer` MUST NOT contain a unit/SKU-to-buy
  claim. Asserted with a numeric-claim probe (a regex over `\d+\s*(unidades|SKUs)` restricted to the
  "a reponer" phrasing), not by comparing against a golden sentence.
- **Surface coherence**: `dashboard is not None ⇒ scope is not None`, and that `scope` is the scope
  the dashboard was computed from (§4c).
- `horizon_days` echoes the scope.
- `interpretation.disambiguation_options` non-empty exactly when `mode == "disambiguation"`.

**frontend `applyChatScope`** (Vitest, `frontend/src/lib/applyChatScope.test.ts`)
- The TS side asserts the mirror of the same rule: a response carrying a `dashboard` replaces the
  panel; a response carrying neither `scope` nor `dashboard` leaves the panel untouched. The
  fixtures are hand-written `ChatResponse` shapes — the TS tests do not read the catalog.

## 4. Product fixes (policies on recorte shape, no rubros)

### (a) Name hits vs the taxonomy node that contains them

*Symptom:* a token resolves to a tiny `sku_set` of name matches while a real category/subcategory
containing all of those SKUs exists.

*Why:* `resolve_single_reference` (`app/pipeline/reference_resolver.py`) consults `_pick_best_group`
**by label score only**. When the token does not match any category *label* well enough
(`MIN_GROUP_SCORE`), the function falls through to the `len(name_hits) >= 2` branch and returns
`_group_from_name_hits(...)` with `scope_dimension="sku_set"` — even though every hit lives under one
category. The resolver never asks *where the hits live*.

*Policy (shape, not strings):* **containment beats lexical score.** Before returning a name-hit
`sku_set`, compute the taxonomy distribution of `name_hits`:

```
hits ⊂ one subcategory (≥ FAMILY_CONTAINMENT of hits, single node)  → resolve to that subcategory
hits ⊂ one category    (same test one level up)                     → resolve to that category
hits spread over ≥2 nodes at both levels                            → keep sku_set (correct today)
```

Implementation: a new `_family_from_name_hits(token, name_hits)` helper next to
`_group_from_name_hits`, called from the `len(name_hits) >= 2` branch of `resolve_single_reference`
and from the fallthrough in `_resolve_conjunction`. It reuses the `category`/`subcategory` indexes
already built by `_collect_entity_indexes`, so no extra catalog pass. The promoted reference keeps
`name_tokens=[token]` so the user's word still shows in the label and the scope keeps the token as a
refinement handle; the *dimension* changes, the *intent* does not.

`FAMILY_CONTAINMENT` (a ratio, e.g. 0.9) and the existing `MIN_GROUP_SCORE` family of constants stay
together at the top of the module. The oracle's containment assertion (§3) is what proves the policy
generalises: for **every** generated name-token contract, the resolved `sku_ids` must be a superset
of the raw hits.

### (b) Empty purchase: no claim, no `draft_oc`

*Symptom:* an empty recorte still narrates a SKU-to-buy count and still offers "¿Armamos la OC?".

*Why:* the turn computes its slice **more than once** and reads emptiness from more than one field.
`runner.run_supplymate` calls `guidance_for_resolution(resolved, scope)`, which internally builds a
**second** `ReplenishmentSlice` (`limit=25`) and whose decision then overrides the one already inside
`slice_data`; `format_explore_answer` derives `sku_hint` from `dashboard.purchase_skus` while its
`empty_purchase` flag is derived from a different combination of the same fields. Three readers, three
chances to disagree.

*Policy:* **one slice per turn, one definition of empty.**

1. `app/agent/runner.py` builds the `ReplenishmentSlice` once and passes it to guidance instead of
   letting `guidance_for_resolution` rebuild it. `guidance_for_resolution` keeps its signature for
   callers that only have a scope, but gains a slice-accepting path so the explore route never
   double-computes.
2. `app/agent/explore_answer.py`: a single `has_purchase = bool(slice_data.purchase_list)` gate.
   Every unit/SKU claim is derived from `slice_data.purchase_list` and `dashboard` fields that are
   zero whenever the list is empty; `dashboard.purchase_skus` is used only to say *how many more are
   in the panel*, never to assert that something must be bought.
3. `app/guidance/engine.py`: move the empty-purchase check **above** the mission-complement branch in
   `pick_next_question`. Today an empty recorte can still reach the complement branch and quote
   `preview_union` units. `_draft_oc_decision` additionally asserts non-empty input (defensive; the
   reordering already makes it unreachable).
4. `app/services/scoping/suggested_filters.py` already gates `ACTION_DRAFT_OC` on `recorte_qty > 0`;
   the oracle pins that as an invariant so it cannot regress.

No copy is hardcoded in the test: the assertion is "no unit/SKU-to-buy claim", and the guidance
action is compared as an enum.

### (c) Panel replacement for non-purchase modes

*Symptom:* a `sales_categories` turn leaves the Explore panel showing the previous recorte's
replenishment KPIs and chart.

*Why, on both sides:*
- Server: `_run_top_categories` returns a `dashboard` computed on the **root** scope but omits
  `scope`. The response says "here is a panel" and "the recorte did not change" at the same time.
- Client: `applyChatScope` returns `current` untouched when `res.scope == null`, while
  `routes/index.tsx` independently sets `chatBoard` from `res.dashboard`. The chips keep describing
  the old recorte while the KPIs describe a different one.

*Policy — a response's panel and its recorte are one payload:*

- **Server invariant:** any `ChatResponse` carrying a `dashboard` MUST carry the `scope` that
  dashboard was computed from. `_run_top_categories` therefore returns `scope=AnalyticalScope()`
  (root) explicitly. This is stated for *all* modes, so a future `mode` inherits the rule instead of
  needing its own branch.
- **Client invariant:** `applyChatScope` decides on the *pair*, not on the mode name:

```
res.scope != null                    → replace panel from res.scope        (today)
res.scope == null && res.dashboard   → replace panel with the root recorte (new; defensive)
res.scope == null && !res.dashboard  → keep panel                          (single SKU, errors)
```

  The `buyOnly` special case for `mode === "list"` stays as the one purchase-specific rule, because
  `buyOnly` is a UI toggle with no field on `AnalyticalScope`. `routes/index.tsx` stops deriving
  `chatBoard` independently and uses the branch `applyChatScope` already decided, so chips, KPIs and
  chart come from a single decision.

*Follow-up continuity* (the risk named in the proposal): the invariant is about **the turn that
carries a panel**, not about wiping history. A refinement that resolves inside the previous recorte
still arrives with `relation == "refinement"` and a scope built on top of `previous` by
`build_scope`, so the panel it replaces is its own superset. A `sales → refinement` two-turn contract
covers exactly this.

## 5. Cleanup

### Archive shipped changes

```
git mv openspec/changes/explore-next-step-chips openspec/changes/archive/2026-09-11-explore-next-step-chips
git mv openspec/changes/wire-chat-scope        openspec/changes/archive/2026-09-11-wire-chat-scope
```

Naming matches the existing convention (`archive/YYYY-MM-DD-<change-name>`, e.g.
`archive/2026-09-10-semantic-correctness`). Each archived folder gets an `archive-report.md` like its
neighbours, naming the green tests that cover the behaviour. Precondition per the proposal: archive
only with tasks 17/17 and 11/11 checked **and** green coverage.

Spec promotion into `openspec/specs/` (which already holds `dashboard-totals`, `react-adapter`,
`slice-api`):

| From | To | Action |
|------|----|--------|
| `changes/explore-next-step-chips/specs/suggested-filters/spec.md` | `specs/suggested-filters/spec.md` | new capability |
| `changes/wire-chat-scope/specs/chat-scope-apply/spec.md` | `specs/chat-scope-apply/spec.md` | new capability |
| `changes/{explore-next-step-chips,wire-chat-scope}/specs/react-adapter/spec.md` | `specs/react-adapter/spec.md` | merge both deltas into the existing file |

The `react-adapter` merge is manual: two deltas, one existing spec. This change's own `react-adapter`
delta (the §4c panel rule) is applied on top and stays in `changes/` until this change is archived.

### Archive dated QA notes

```
docs/operations/qa-consulta-desodorantes-2026-09-10.md → docs/operations/archive/qa-consulta-desodorantes-2026-09-10.md
docs/operations/estado-superficies-2026-09-10.md       → docs/operations/archive/estado-superficies-2026-09-10.md
```

`docs/README.md` rows 25–26 are removed from the index (dated snapshots are history, not
navigation). The undated operations docs stay.

### Stale Streamlit copy

| File | Change |
|------|--------|
| `docs/templates/change-request-template.md` | drop the `\| Streamlit \| \|` surface row |
| `docs/README.md` | drop the two dated rows above (both mention Streamlit) |
| `frontend/src/lib/scope-label.ts` | reword the header comment; the policy statement stands on its own without the retired-surface contrast |

`openspec/config.yaml` keeps "Streamlit is retired (not a product surface)". That line is the guard
that prevents reintroduction, not stale copy — the success criterion is read as *no reference that
implies Streamlit is a live surface*.

### Golden CSVs frozen

`docs/contract/evaluation.md` and `.es.md` gain a short section: the four CSVs under `tests/golden/`
(`intents`, `multiturn`, `query_interpretation`, `reference_resolution`) are **frozen in row count**;
new regression cases go to `tests/golden/traps/` or to a generated contract. Same section documents
the oracle and restates the no-judge rule (Groq paraphrases inputs; Python scores).

## 6. Test layout

```
tests/evals/recorte/
  __init__.py
  conftest.py            # session-scoped store, --recorte-seed option
  axes.py                # live-catalog axis enumeration
  contracts.py           # Contract model, pairwise selection, seed, cap
  pipeline.py            # thin call-throughs at both depths
  oracle.py              # the predicates in §3
  catalog_shape.json     # coarse drift snapshot
  test_resolution_contracts.py   # depth = resolution, parametrized over contracts
  test_turn_contracts.py         # depth = turn
  test_catalog_drift.py          # asserts catalog_shape.json
  test_llm_paraphrase.py         # @pytest.mark.llm, RUN_LLM_EVALS=1, same oracle

tests/golden/traps/
  traps.csv
  test_traps.py

tests/unit/agent/test_explore_answer.py          # extended: empty-purchase claim integrity  (RED for 4b)
tests/unit/agent/test_top_categories_surface.py  # new: sales carries its scope              (RED for 4c)
tests/integration/reference_resolution/test_reference_resolver.py  # extended: family containment (RED for 4a)
frontend/src/lib/applyChatScope.test.ts          # new: panel replacement pairs              (RED for 4c, client)
```

Markers: `combinatorial_full` is added to `pyproject.toml` alongside `performance` and `llm`. CI
stays `pytest -m "not performance and not llm"` and gains nothing that needs Groq; the `-m
combinatorial_full` set is opt-in. Generated tests are parametrized with a stable `id` derived from
the contract's axis values so a failure names the combination.

## 7. Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Committed contract snapshot (JSON of ~200 frozen cases) | Freezes rubros — the exact failure mode the proposal forbids. Kept only as the coarse shape snapshot. |
| Full cartesian in CI | Thousands of turn-depth cases; each builds a slice over ~13k SKUs. Blows the performance budget for marginal extra signal over 2-wise. Available behind a marker. |
| Hypothesis / property-based generation instead of pairwise | Non-reproducible failure ids without a database, and shrinking over catalog values produces confusing minimal cases. A fixed seed plus a printed axis tuple is easier to act on. |
| LLM-as-judge over answers | Explicitly out of scope (Engram decision #944). The LLM may only paraphrase contract inputs. |
| Fix (a) by adding a category alias table (token → category) | A hardcoded rubro map by another name; breaks on the next CSV. Containment is a shape rule. |
| Fix (b) by suppressing copy in `format_explore_answer` only | Leaves the double-slice divergence that produced the mismatch; guidance would still offer `draft_oc`. |
| Fix (c) by branching on `mode === "sales"` in the frontend | Special-cases one mode; the next non-purchase mode reintroduces the bug. The `scope`/`dashboard` pair rule is mode-agnostic. |
| Snapshot-testing whole `ChatResponse` payloads | Turns every catalog edit into a diff review and reintroduces golden-phrase coupling. |

## 8. Risks and migration

| Risk | Mitigation |
|------|------------|
| Family policy (4a) over-promotes: a token that legitimately means a handful of SKUs across one big category now returns the whole category | The containment ratio is high (single node, ≥ `FAMILY_CONTAINMENT` of hits) and the promoted ref keeps `name_tokens`, so the scope still carries the token. Contracts assert *containment*, so a too-eager promotion that swallows unrelated SKUs is not detected by containment alone — the `xxg`/`xxxg` trap and a "hits spread over ≥2 nodes stays `sku_set`" contract cover the other direction. |
| Reordering guidance branches (4b) changes copy on non-empty recortes | The empty check is inserted as an early return on a condition that is false for every non-empty slice, so non-empty behaviour is untouched; existing `tests/integration/guidance/test_guidance_plan.py` is the regression net. |
| Panel replacement (4c) regresses follow-up continuity | Two-turn `sales → refinement` contract; plus the rule triggers only when the response actually carries a `dashboard`. |
| Single-slice refactor in `runner.py` touches a god node (`run_supplymate`) | Change is limited to how `guidance_for_resolution` is fed; routing branches are untouched. `tests/integration/agent/test_agent.py` and `tests/acceptance/` run before and after. |
| Pairwise runtime creeps as the catalog grows | Session-scoped store; resolution-depth contracts dominate; the 200 cap is enforced, not advisory; `tests/performance/` thresholds are the backstop. |
| Archiving a change that is not truly shipped | Archive only at 100 % tasks **and** green coverage, with an `archive-report.md` naming the tests. |
| Two `react-adapter` deltas merged by hand into one promoted spec | Merge is a reviewed step in tasks, not a script; the promoted spec is read once against both deltas. |

**Migration:** none for runtime data or API contracts. `ChatResponse.scope` becomes non-null for the
sales route, which is additive for existing clients (the frontend already handles a present `scope`).
No model field is added or removed. After code edits, run `graphify update .`.
