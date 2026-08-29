# Tools Spec

## ADDED Requirements

### Requirement: Get inventory by product

The system MUST return structured inventory for a known product_id from CSV.

#### Scenario: Valid product inventory

- **GIVEN** product_id PROD-001 exists in inventory.csv
- **WHEN** get_inventory is called
- **THEN** the response MUST include product_id and current_stock

### Requirement: Get sales history by product

The system MUST return sales rows for a product filtered to the requested recent day window (default 30).

#### Scenario: Valid sales history

- **GIVEN** product_id PROD-001 has sales history
- **WHEN** get_sales_history is called with days=30
- **THEN** the response MUST include product_id and a non-empty list of date/units_sold entries within the window

### Requirement: Get replenishment params by product

The system MUST return lead_time_days and safety_stock for a known product_id.

#### Scenario: Valid replenishment params

- **GIVEN** product_id PROD-001 exists in replenishment_params.csv
- **WHEN** get_replenishment_params is called
- **THEN** the response MUST include product_id, lead_time_days, and safety_stock

### Requirement: Unknown product handling

Tools MUST fail clearly when product_id is not found.

#### Scenario: Unknown product id

- **GIVEN** product_id PROD-999 does not exist
- **WHEN** any data tool is called for that id
- **THEN** the tool MUST raise an error indicating the product was not found
