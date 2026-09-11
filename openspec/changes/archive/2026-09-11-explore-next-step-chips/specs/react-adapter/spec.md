# Delta for react-adapter

## ADDED Requirements

### Requirement: Explore prompt chips from slice suggested_filters

With FastAPI up, Explore MUST show slice `suggested_filters` in a 3×2 grid (max 6), hide the strip when empty, and MUST NOT pad dummy or hardcoded default chips.

#### Scenario: Live chips

- GIVEN a live slice with four `suggested_filters`
- WHEN chips render
- THEN four chips MUST show those labels in order

#### Scenario: Empty hides

- GIVEN zero live `suggested_filters` or no applicable mock slots
- WHEN chips would render
- THEN the strip MUST be hidden

### Requirement: Chip click applies the action, not chat

Click MUST apply `action`/`args` and MUST NOT send chip text to chat. `filter_*` MUST update UiSlice. `open_sku` MUST open the SKU drawer. `draft_oc` MUST open the PO flow.

#### Scenario: Filter

- GIVEN a `filter_category` chip for `Cuidado`
- WHEN clicked
- THEN UiSlice MUST include `Cuidado` and chat MUST NOT receive the label

#### Scenario: Open SKU

- GIVEN an `open_sku` chip
- WHEN clicked
- THEN the SKU drawer MUST open for that product

#### Scenario: Draft OC

- GIVEN a `draft_oc` chip
- WHEN clicked
- THEN the PO surface MUST open

### Requirement: Offline mock equivalent chips

Catálogo demo chips MUST use the same ranking and skip-active rules on mock rows. Qty MUST still come from mock `compute()`. MUST NOT invent a second formula.

#### Scenario: Mock ranking

- GIVEN demo rows with unused categories
- WHEN chips render
- THEN order MUST match live ranking and qty MUST still come from mock `compute()`
