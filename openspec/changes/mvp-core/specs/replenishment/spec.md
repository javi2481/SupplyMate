# Replenishment Spec

## ADDED Requirements

### Requirement: Average daily demand

The system MUST compute average daily demand as total units sold in the last 30 days divided by 30.

#### Scenario: Happy path average

- **GIVEN** a product sold 750 units over the last 30 days
- **WHEN** average daily demand is calculated
- **THEN** average daily demand MUST equal 25.0

### Requirement: Demand components and stock target

The system MUST compute:
- horizon demand = average_daily_demand × 7
- lead-time demand = average_daily_demand × lead_time_days
- stock_target = horizon demand + lead-time demand + safety_stock

#### Scenario: Stock target with lead time and safety

- **GIVEN** average daily demand 25, lead_time_days 3, safety_stock 50
- **WHEN** stock target is calculated
- **THEN** horizon demand MUST be 175, lead-time demand MUST be 75, and stock_target MUST be 300

### Requirement: Recommended order quantity

The system MUST compute recommended_quantity as max(0, stock_target − current_stock).

#### Scenario: Positive order quantity

- **GIVEN** stock_target 300 and current_stock 170
- **WHEN** recommended quantity is calculated
- **THEN** recommended_quantity MUST equal 130

#### Scenario: Stock exceeds target

- **GIVEN** stock_target 300 and current_stock 500
- **WHEN** recommended quantity is calculated
- **THEN** recommended_quantity MUST equal 0
