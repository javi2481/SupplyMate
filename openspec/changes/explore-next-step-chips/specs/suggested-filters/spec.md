# Suggested Filters Specification

## Requirements

### Requirement: Cap six, no LLM, no padding

`suggest_next_filters` MUST return at most six `SuggestedFilter` items. It MUST NOT call an LLM or `Runner`, invent values, or pad dummy chips to six.

#### Scenario: Sparse

- GIVEN two applicable slots
- WHEN suggestions are built
- THEN the list MUST have two items

#### Scenario: Overflow

- GIVEN more than six applicable slots
- WHEN suggestions are built
- THEN the list MUST be the first six in rank order

### Requirement: Skip active scope filters

`filter_*` candidates MUST be omitted when that value is already in `AnalyticalScope`. `open_sku` and `draft_oc` MUST still be considered if their conditions hold.

#### Scenario: Active category

- GIVEN the top `by_category` is already in `scope.categories`
- WHEN suggestions are built
- THEN that category MUST NOT appear

### Requirement: Ranking order

First-applicable, cap 6; omit a slot when absent: (1) first unused `by_category` by recommended qty; (2) second unused `by_category`; (3) coverage `0–3 días` if `sku_count > 0`, else next populated unused bar; (4) `stockout_risk` if > 0; (5) `overstock` if > 0; (6) top unused purchase-list supplier; (7) top purchase-list item `open_sku`; (8) `draft_oc` if recorte recommended qty > 0.

#### Scenario: Cap

- GIVEN unused categories A,B, 0–3 coverage, stockout, overstock, unused supplier, top SKU, recorte qty > 0
- WHEN suggestions are built
- THEN items MUST be A, B, coverage, stockout_risk, overstock, supplier
- AND `open_sku` and `draft_oc` MUST be omitted

#### Scenario: Draft OC only

- GIVEN no unused filter or SKU candidates and recommended qty > 0
- WHEN suggestions are built
- THEN the list MUST be one `draft_oc` item

### Requirement: Question-style labels

Each `label` MUST be a short question-style prompt. It MUST NOT use `Ver … — N SKUs · u.`

#### Scenario: Category copy

- GIVEN unused category `Cuidado`
- WHEN that chip is emitted
- THEN `label` MUST ask about `Cuidado`

### Requirement: Payload

Each item MUST have `action`, `args`, `label`. Actions: `filter_category`, `filter_coverage`, `filter_health`, `filter_supplier`, `open_sku`, `draft_oc`. Args MUST match the action and snap/item values (`category`, `coverage_bucket`, `health_bucket`, `supplier`, `product_id`; empty for `draft_oc`).

#### Scenario: Overstock

- GIVEN overstock > 0, not active, within cap
- WHEN that chip is emitted
- THEN action MUST be `filter_health` and `health_bucket` MUST be `overstock`
