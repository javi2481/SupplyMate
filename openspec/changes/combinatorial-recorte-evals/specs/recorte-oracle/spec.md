# Delta for recorte-oracle

New capability. A deterministic Python oracle that asserts recorte and surface
invariants over combinations generated from the live catalog. Requirements below
are policies on the **shape** of the recorte; no requirement may name a concrete
category, subcategory, supplier, SKU, or answer phrase as its subject.

## ADDED Requirements

### Requirement: Contracts are generated from the live catalog

The contract generator MUST derive every axis value by enumerating the live
`CatalogStore` at test time (categories, subcategories, suppliers, coverage and
health buckets, name tokens sampled from product names). It MUST NOT contain a
literal category, subcategory, supplier, SKU id, or expected answer phrase.
Expectations MUST be relations over the produced recorte (which
`scope_dimension` won, set containment, count comparisons, which surfaces and
offers are allowed), and MUST NOT be absolute values copied from a fixture.
Only `tests/golden/traps/` MAY name concrete catalog values, and only as named
regressions for known bugs.

#### Scenario: Generator holds no frozen rubro

- **GIVEN** the contract generator module
- **WHEN** the eval suite is collected
- **THEN** every axis value MUST originate from a `CatalogStore` lookup
- **AND** a static scan of the generator MUST find no literal category,
  subcategory, supplier, or SKU string

#### Scenario: Catalog rename does not break the suite

- **GIVEN** a catalog CSV in which a taxonomy label is renamed
- **WHEN** contracts are regenerated
- **THEN** contracts MUST be produced for the renamed value
- **AND** assertions MUST stay relational (for example, the containing family's
  SKU set is a superset of the name hits)
- **AND** no assertion MUST depend on an absolute per-node SKU count

### Requirement: Pairwise axis coverage under a fixed budget

The runner SHALL cover the axes taxonomy (category or subcategory), supplier,
coverage/health bucket, horizon, turn relation (`new_query` or `refinement`),
intent surface (purchase versus sales), and resolvability (resolvable or
unresolved token). It MUST cover every pair (2-wise) of axis values using a
fixed seed so the generated set is byte-identical across runs on the same
catalog. The default run MUST be capped (about 200 contracts) so the suite stays
inside the existing performance budget, and MUST reuse a single `CatalogStore`
instance across contracts. The full cartesian product MAY run only behind an
opt-in marker (`-m combinatorial_full`).

#### Scenario: Deterministic contract set

- **GIVEN** an unchanged catalog and the fixed seed
- **WHEN** the generator runs twice
- **THEN** both runs MUST produce the same ordered contract set
- **AND** every pair of axis values MUST appear in at least one contract

#### Scenario: Full matrix is opt-in

- **GIVEN** the default marker expression `not performance and not llm`
- **WHEN** the suite runs
- **THEN** only the capped pairwise set MUST execute
- **AND** the full cartesian set MUST be skipped unless `-m combinatorial_full`
  is requested

### Requirement: Python is the sole oracle over the real pipeline

Each contract MUST execute the production path
`interpret_query_llm → resolve_references → build_scope → replenishment_slice`
(and `run_supplymate` when the contract asserts `ChatResponse`). Assertions MUST
be Python over the typed objects `ResolvedReference`, `AnalyticalScope`,
`ReplenishmentSlice`, and `ChatResponse`. The oracle MUST NOT call a model to
decide pass or fail, MUST NOT score prose quality, and MUST pass with no network
and no Groq key. Claims about the answer string MUST be structural only
(whether a unit or SKU count is claimed, whether an offer is present), never
phrase equality.

#### Scenario: Contract asserts typed shape

- **GIVEN** a generated contract for one taxonomy value plus one health bucket
- **WHEN** the contract runs the pipeline
- **THEN** the oracle MUST assert `ResolvedReference.scope_dimension`,
  `AnalyticalScope` fields, `ReplenishmentSlice.dashboard` counters, and
  `ChatResponse.mode`
- **AND** MUST NOT compare the answer to a stored sentence

#### Scenario: No model call in the default run

- **GIVEN** no Groq credentials in the environment
- **WHEN** `pytest -m "not performance and not llm"` runs
- **THEN** the oracle suite MUST pass
- **AND** MUST NOT issue an outbound model request

### Requirement: A matching taxonomy family wins over a tiny name-hit set

When a reference token produces name hits **and** at least one taxonomy node
(category or subcategory) whose normalized label matches the same token and
whose SKU set contains those name hits, `resolve_references` MUST return that
taxonomy node: `scope_dimension` MUST be `category` or `subcategory`,
`scope_value` MUST be the node label, and `sku_count` MUST be greater than or
equal to the name-hit count. A `sku_set` resolution MUST be produced only when
no matching taxonomy node exists, or when no matching node contains the hits
(for example, cross-taxonomy attribute tokens such as sizes or formats). This
policy MUST be expressed over label matching and set containment and MUST NOT
branch on any specific rubro.
<!-- Illustrative repro from QA tanda 5: the token "toallitas" previously
     resolved to a handful of name hits while a same-named family existed. -->

#### Scenario: Family preferred over name hits

- **GIVEN** a generated token whose normalized form matches a taxonomy node
  label and whose name hits are a proper subset of that node's SKUs
- **WHEN** the reference is resolved
- **THEN** `scope_dimension` MUST be the taxonomy dimension of that node
- **AND** `sku_count` MUST be greater than or equal to the number of name hits
- **AND** `scope_dimension` MUST NOT be `sku_set`

#### Scenario: Attribute token still resolves to a SKU set

- **GIVEN** a generated token that matches product names across more than one
  taxonomy node and matches no node label
- **WHEN** the reference is resolved
- **THEN** `scope_dimension` MAY be `sku_set`
- **AND** `name_tokens` MUST carry the token
- **AND** the resulting SKU set MUST contain only products whose name matches
  the token exactly under the resolver's token rule

#### Scenario: Containment invariant holds for every contract

- **GIVEN** any contract whose axis value is a name token
- **WHEN** the resolution completes
- **THEN** the resolved SKU set MUST be a subset of the SKUs of the smallest
  taxonomy node that contains all of its name hits, when such a node exists
- **AND** the resolution MUST NOT return fewer SKUs than that node when the node
  label matches the token

### Requirement: An empty recorte MUST NOT claim SKUs or units

When the applied slice is empty (`purchase_list` is empty **and**
`dashboard.purchase_skus` is 0), the answer MUST state that nothing in the
recorte requires replenishment. It MUST NOT state a count of SKUs to replenish,
MUST NOT state a number of units to order, and MUST NOT derive such a claim from
per-reference `group_summaries`. It MAY name the recorte and MAY report the
number of SKUs the recorte contains, provided that number is not presented as a
replenishment quantity.

#### Scenario: Empty purchase does not narrate a purchase

- **GIVEN** a contract whose axis combination yields an empty purchase list with
  `dashboard.purchase_skus == 0`
- **WHEN** the answer is formatted
- **THEN** it MUST contain the nothing-to-replenish statement
- **AND** it MUST NOT contain a "N SKUs a reponer" or "N unidades a reponer"
  claim
- **AND** `group_summaries` totals MUST NOT be rendered as a purchase claim

#### Scenario: Non-empty purchase keeps its counters

- **GIVEN** a contract whose slice has at least one purchase line
- **WHEN** the answer is formatted
- **THEN** the claimed SKU count MUST equal `dashboard.purchase_skus`
- **AND** the claimed unit total MUST equal `dashboard.recommended_units`

### Requirement: An empty recorte MUST NOT offer a purchase order

When the applied slice is empty, `GuidanceDecision.action` MUST NOT be
`draft_oc`, the response MUST NOT include a `draft_oc` chip, and the answer MUST
NOT ask whether to build the order. The offered next step SHOULD be an action
that widens or changes the recorte.

#### Scenario: No OC offer on an empty recorte

- **GIVEN** a contract whose slice is empty
- **WHEN** guidance is computed and the response is assembled
- **THEN** `guidance.action` MUST NOT be `draft_oc`
- **AND** no `GuidanceChip` with action `draft_oc` MUST be present
- **AND** the answer MUST NOT contain an order-building offer

#### Scenario: OC offer survives on a non-empty recorte

- **GIVEN** a contract whose slice has purchase lines and no pending facet
  question
- **WHEN** guidance is computed
- **THEN** `guidance.action` MAY be `draft_oc`

### Requirement: Every mode carries an explicit panel surface

A `ChatResponse` MUST carry the payload its mode needs to render a panel, so the
client never has to infer "keep the previous panel". Recorte-owning modes MUST
carry both `scope` and `dashboard`. A mode that renders a different surface
without a purchase recorte (for example the sales ranking) MUST carry its own
`dashboard` and MUST carry an explicit `scope` describing the recorte it
computed (the empty `AnalyticalScope` when it computed over the whole catalog).
A response MUST NOT be ambiguous between "nothing changed" and "a different
surface applies".

#### Scenario: Sales turn carries its surface

- **GIVEN** a contract whose intent axis is the sales ranking
- **WHEN** `run_supplymate` returns
- **THEN** `mode` MUST be `sales`
- **AND** `dashboard` MUST carry the sales bars it computed
- **AND** `scope` MUST be present and MUST describe the recorte actually used
- **AND** the answer MUST NOT claim replenishment counters from a prior turn

#### Scenario: Conversational turn carries no surface

- **GIVEN** a contract whose token is unresolved and the turn only asks a
  question
- **WHEN** the response is assembled
- **THEN** both `scope` and `dashboard` MAY be absent
- **AND** the response MUST NOT carry a partial surface (a dashboard without the
  scope it was computed for)

### Requirement: Horizon is echoed by scope and response

When the query carries an explicit horizon, the resulting
`AnalyticalScope.horizon_days` and `ChatResponse.horizon_days` MUST equal that
horizon and the slice MUST be computed with it. When no horizon is stated, both
MUST be the default of 7. A refinement turn without a new horizon MUST retain
the horizon of the prior turn.

#### Scenario: Explicit horizon propagates

- **GIVEN** a contract whose horizon axis is a value other than the default
- **WHEN** the turn completes
- **THEN** `scope.horizon_days` and `ChatResponse.horizon_days` MUST equal it
- **AND** the answer MUST reference the same horizon it computed with

#### Scenario: Refinement inherits the horizon

- **GIVEN** a first turn with an explicit horizon and a follow-up classified as
  `refinement` that states no horizon
- **WHEN** the follow-up completes
- **THEN** `scope.horizon_days` MUST still equal the first turn's horizon

### Requirement: A refinement retains the prior recorte

When the turn relation is `refinement`, the resulting scope MUST retain the
filter dimensions of the prior scope and add or narrow at most the dimensions
the follow-up names. It MUST NOT reset to the empty recorte. When the relation
is `new_query`, prior filters MUST be dropped. A refinement that follows a turn
which replaced the panel surface without a purchase recorte MUST retain the
recorte that was in force before that turn.

#### Scenario: Follow-up narrows instead of resetting

- **GIVEN** a first turn that establishes a taxonomy recorte and a follow-up
  classified as `refinement` naming a health bucket
- **WHEN** the follow-up completes
- **THEN** the scope MUST contain both the taxonomy value and the health bucket
- **AND** the scope MUST NOT be empty

#### Scenario: Refinement after a surface replacement

- **GIVEN** a recorte in force, then a sales-ranking turn, then a follow-up
  classified as `refinement`
- **WHEN** the follow-up completes
- **THEN** the scope MUST be the pre-existing recorte plus the new filter
- **AND** MUST NOT be the whole catalog

#### Scenario: New query drops prior filters

- **GIVEN** a recorte in force and a follow-up classified as `new_query`
- **WHEN** the turn completes
- **THEN** the prior filter dimensions MUST NOT survive in the new scope

### Requirement: An unresolved reference yields disambiguation

When a reference matches no taxonomy node, supplier, or product name at the
resolver's confidence threshold, the `ResolvedReference` MUST have
`match_kind = "unresolved"`, `ChatResponse.mode` MUST be `disambiguation`, and
the answer MUST ask which entity was meant. The turn MUST NOT narrow the scope
on a guess, MUST NOT present KPIs or quantities, and MUST NOT offer `draft_oc`.

#### Scenario: Unknown token asks instead of guessing

- **GIVEN** a contract whose resolvability axis is an unresolvable token
- **WHEN** the turn completes
- **THEN** `mode` MUST be `disambiguation`
- **AND** the scope MUST equal the prior scope (unchanged)
- **AND** the answer MUST NOT contain a replenishment quantity

### Requirement: Named trap goldens for known regressions

`tests/golden/traps/` SHALL hold a small, explicitly named list of known bugs.
Each trap MUST name the buggy behavior, MUST assert the invariant version of the
fix (a shape relation), and MUST NOT assert an answer phrase. Traps MUST be
additive files; the four existing golden CSVs MUST NOT grow.
<!-- Current traps: unresolved supplier token; an exact size token must not match
     a longer size token; family-over-name-hit resolution. -->

#### Scenario: Trap asserts the invariant, not the phrase

- **GIVEN** a trap entry for a known resolution bug
- **WHEN** the trap runs
- **THEN** it MUST assert the resolved dimension and set relation
- **AND** MUST NOT compare the answer text to a stored sentence

#### Scenario: Golden CSVs stay frozen

- **GIVEN** the four existing golden CSVs
- **WHEN** this change is verified
- **THEN** their row counts MUST be unchanged
- **AND** new regressions MUST land in `tests/golden/traps/` or as generated
  contracts

### Requirement: Coarse catalog drift snapshot

A committed snapshot SHALL record only coarse catalog shape (number of
categories, subcategories and suppliers, total SKUs, and the canonical coverage
and health bucket names). A mismatch MUST fail with a message naming which
dimension drifted and how to refresh the snapshot. The snapshot MUST NOT record
per-node SKU counts or node labels used as expectations.

#### Scenario: Drift fails loudly and actionably

- **GIVEN** a catalog CSV that adds a category
- **WHEN** the drift check runs
- **THEN** it MUST fail naming the drifted dimension and the refresh step
- **AND** the relational contract assertions MUST still pass

### Requirement: The oracle runs in the default CI marker set

The oracle suite MUST be part of `pytest -m "not performance and not llm"`, MUST
keep that command green, and MUST NOT require Groq, network access, or a live
frontend. Its added runtime SHOULD stay inside the existing performance budget;
work that cannot MUST move behind `performance` or `combinatorial_full`.

#### Scenario: Default CI stays green and offline

- **GIVEN** a checkout with no model credentials
- **WHEN** `pytest -m "not performance and not llm"` runs
- **THEN** the oracle contracts and traps MUST execute and pass
