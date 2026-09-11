# Spec: react-adapter

## Requirements

### Requirement: Visual projection without domain math

Given a `PurchaseListItem` from FastAPI, the adapter MUST produce a visual row
for the ops table without inventing replenishment intermediates
(`demand_horizon`, `demand_lead`, `stock_target`, `lead_time_days`,
`safety_stock`). Those fields MAY only appear after
`GET /products/{id}/replenishment`.

#### Scenario: Table row from purchase list

- **GIVEN** a `PurchaseListItem` with `recommended_quantity`, `current_stock`,
  `days_of_supply`, `operational_priority`, `health_bucket`
- **WHEN** the adapter maps it to a list row
- **THEN** qty, stock, coverage, and priority label MUST come from the item
- **AND** demand/lead/safety fields MUST be absent or null until SKU detail loads

### Requirement: Priority labels match backend

#### Scenario: Critical vs high

- **GIVEN** `operational_priority` values `critical`, `high`, `normal`
- **WHEN** labels are rendered
- **THEN** they MUST be `Crítica`, `Alta`, `Normal` respectively
- **AND** MUST NOT map both `critical` and `high` to the same label

### Requirement: Health labels match backend

#### Scenario: Understock copy

- **GIVEN** `health_bucket === "understock"`
- **WHEN** the health chip is shown
- **THEN** the label MUST be `Falta de stock`

### Requirement: KPI clicks do not compute qty

#### Scenario: Filter only

- **GIVEN** the operator clicks a KPI (e.g. stockout risk)
- **WHEN** the slice updates
- **THEN** recommended quantities MUST still come from the API (or mock catalog in offline mode)
- **AND** the UI MUST NOT recompute order-up-to in TypeScript on the happy path

### Requirement: SKU drawer uses replenishment endpoint

#### Scenario: Open SKU detail with API up

- **GIVEN** FastAPI is reachable
- **WHEN** the operator opens a SKU drawer
- **THEN** calculation facts MUST load from `GET /products/{id}/replenishment`

### Requirement: CSV export uses the same scope

#### Scenario: Export PO

- **GIVEN** an active AnalyticalScope (categories, coverage, health, …)
- **WHEN** Export CSV is clicked with API up
- **THEN** the download URL MUST use the same query params as the current slice

### Requirement: Offline fallback hides API URL

The previous demo-catalog fallback is removed.

#### Scenario: API down

- **GIVEN** the slice fetch fails
- **WHEN** chrome shows status
- **THEN** it MUST say `Sin catálogo`
- **AND** MUST NOT display localhost / API host strings
- **AND** MUST NOT say Catálogo demo

### Requirement: Coverage chips match COVERAGE_ORDER

Explore coverage chips MUST be the five canonical `COVERAGE_ORDER` labels
(`0–3 días`, `3–7 días`, `7–14 días`, `14–30 días`, `30+ días`) with Unicode
en-dash. The UI MUST NOT render a `14+` chip that spans two backend bands.

#### Scenario: Five chips, canonical labels

- **GIVEN** the Explore filter row
- **WHEN** coverage chips render
- **THEN** there MUST be exactly five chips whose labels are `COVERAGE_ORDER`
- **AND** MUST NOT render a `14+` chip

#### Scenario: One chip, one bucket

- **GIVEN** the operator selects `14–30 días`
- **WHEN** `sliceToScopeQuery` / `fetchSlice` / CSV URL are built
- **THEN** `coverage_bucket` MUST be exactly `["14–30 días"]`
- **AND** MUST NOT also include `30+ días`

#### Scenario: Mock fallback uses the same edges

- **GIVEN** API down and Catálogo demo
- **WHEN** the operator selects `30+ días`
- **THEN** only mock rows with `coverageBandFromDays(days) === "30+ días"` remain
- **AND** qty still comes from mock `compute()`, never from a second formula

### Requirement: Unidades KPI uses dashboard recorte totals

When FastAPI is reachable, Explore `Unidades a pedir` MUST use
`InventoryDashboard.recommended_units` from the current slice. It MUST NOT
sum `purchase_list` / table rows on the happy path.

#### Scenario: Page is smaller than the recorte

- **GIVEN** a live dashboard with `recommended_units = 17753` and a
  `purchase_list` whose qty sum is 6243
- **WHEN** KPIs render
- **THEN** Unidades MUST show 17753
- **AND** the table MAY still show 50 rows

#### Scenario: Offline mock

- **GIVEN** Catálogo demo
- **WHEN** KPIs render
- **THEN** Unidades MAY sum mock rows (the demo catalog is the full recorte)

### Requirement: Table caption names the recorte sample

#### Scenario: Truncated purchase list

- **GIVEN** `purchase_skus >` visible table rows and no table search
- **WHEN** the table chrome renders
- **THEN** the caption MUST state the page size versus `purchase_skus`
  (e.g. `50 de 1.059 a reponer`)
- **AND** MUST NOT imply the table is the full recorte

### Requirement: Falta de stock KPI uses out_of_stock

When FastAPI is reachable, Explore `Falta de stock` MUST use
`InventoryDashboard.out_of_stock`. Activating the Falta de stock chip MUST send
`out_of_stock=true` on slice and CSV requests. It MUST NOT send
`health_bucket=understock` for that chip.

#### Scenario: Chip filters zero stock

- **GIVEN** Motor listo and the operator activates Falta de stock
- **WHEN** `fetchSlice` / CSV URL are built
- **THEN** the query MUST include `out_of_stock=true`
- **AND** the KPI value MUST equal `dashboard.out_of_stock`

### Requirement: Status chrome hides Catálogo demo while loading live API

When a live API URL is configured and the slice has not failed, product chrome
MUST NOT say `Catálogo demo`. That label is reserved for mock / offline mode.

#### Scenario: First paint with API URL

- **GIVEN** `VITE_SUPPLYMATE_API_URL` is set and the first slice is still loading
- **WHEN** status chrome renders
- **THEN** it MUST NOT display `Catálogo demo`

### Requirement: Seed threads avoid demo catalog names

#### Scenario: Default conversation list

- **GIVEN** a fresh Explore session
- **WHEN** seed thread titles render
- **THEN** they MUST NOT contain Lovable demo category names
  (`Pañales`, `Nutrición`, `Mamaderas`)

### Requirement: CSV export can cover the full recorte

With API up, Export CSV MUST request up to `purchase_skus` rows (capped by the
CSV endpoint max, at least 10_000). The Explore table MAY remain at limit 50.

#### Scenario: Large recorte export

- **GIVEN** `purchase_skus = 5395` and API up
- **WHEN** Exportar orden is clicked
- **THEN** the CSV URL `limit` MUST be `5395` (or the CSV max if lower)
- **AND** MUST NOT be capped at 100

### Requirement: Explore uses only the live catalog

Explore MUST render purchase rows and dashboard from FastAPI `/data`. It MUST NOT render Lovable `CATALOG` / `ROWS` / `compute()` / `answerFor()`.

#### Scenario: Slice fetch fails

- **GIVEN** the slice request fails
- **WHEN** Explore paints
- **THEN** the table MUST be empty
- **AND** chrome MUST say `Sin catálogo`
- **AND** MUST NOT say `Catálogo demo`
- **AND** MUST NOT show Pañales / Mamaderas demo SKUs

### Requirement: Chat drives the recorte

After a successful `/chat`, Explore MUST apply `ChatResponse.scope` and refetch the slice. It MUST NOT call `sliceFromText`.

#### Scenario: Operator types quiebre

- **GIVEN** a live catalog
- **WHEN** the operator sends `quiebre`
- **THEN** UiSlice health MUST follow Python `stockout_risk`
- **AND** the board MUST update from the new slice

### Requirement: Empty and missing copy

#### Scenario: Table search miss

- **GIVEN** no rows match the table search `X`
- **THEN** copy MUST include `No encontramos productos para “X”`

#### Scenario: Empty recorte

- **GIVEN** a loaded slice with zero table rows
- **THEN** copy MUST be `No hay productos en este recorte. Probá quitar un filtro.`

#### Scenario: Chart load failure

- **GIVEN** slice error and no category bars
- **THEN** copy MUST be `No pude cargar las categorías. Intentá de nuevo en un momento.`

### Requirement: Explore prompt chips from slice suggested_filters

With FastAPI up, Explore MUST show slice `suggested_filters` in a 3×2 grid (max 6), hide the strip when empty, and MUST NOT pad dummy or hardcoded default chips.

#### Scenario: Live chips

- **GIVEN** a live slice with four `suggested_filters`
- **WHEN** chips render
- **THEN** four chips MUST show those labels in order

#### Scenario: Empty hides

- **GIVEN** zero live `suggested_filters` or no applicable mock slots
- **WHEN** chips would render
- **THEN** the strip MUST be hidden

### Requirement: Chip click applies the action, not chat

Click MUST apply `action`/`args` and MUST NOT send chip text to chat. `filter_*` MUST update UiSlice. `open_sku` MUST open the SKU drawer. `draft_oc` MUST open the PO flow.

#### Scenario: Filter

- **GIVEN** a `filter_category` chip for `Cuidado`
- **WHEN** clicked
- **THEN** UiSlice MUST include `Cuidado` and chat MUST NOT receive the label

#### Scenario: Open SKU

- **GIVEN** an `open_sku` chip
- **WHEN** clicked
- **THEN** the SKU drawer MUST open for that product

#### Scenario: Draft OC

- **GIVEN** a `draft_oc` chip
- **WHEN** clicked
- **THEN** the PO surface MUST open

### Requirement: Offline mock equivalent chips

Catálogo demo chips MUST use the same ranking and skip-active rules on mock rows. Qty MUST still come from mock `compute()`. MUST NOT invent a second formula.

#### Scenario: Mock ranking

- **GIVEN** demo rows with unused categories
- **WHEN** chips render
- **THEN** order MUST match live ranking and qty MUST still come from mock `compute()`
