# Agent Spec

## ADDED Requirements

### Requirement: Two-phase recommendation flow

The agent MUST gather inventory, sales history, and replenishment params via tools, then apply deterministic Python calculation, then produce a Spanish explanation.

#### Scenario: Quantity comes from Python

- **GIVEN** a user asks how much to order of PROD-001
- **AND** tools return inventory, sales, and params for PROD-001
- **WHEN** the agent flow completes
- **THEN** recommended_quantity MUST equal the Python replenishment result for those inputs
- **AND** the API quantity MUST NOT be parsed from free-form LLM text alone

### Requirement: Explanation uses calculation

The explanation agent MUST receive the calculated result and SHOULD explain using those numbers without inventing alternative quantities for the structured response.
