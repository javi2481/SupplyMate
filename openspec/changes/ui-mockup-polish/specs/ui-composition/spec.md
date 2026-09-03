# Spec: ui-composition

## MODIFIED Requirements

### KPI card metadata

- `KpiCard` MAY expose optional icon metadata for the presentation layer
- Optional icon metadata MUST NOT be required by commit cards or existing tests unrelated to the visual shell

#### Scenario: KPI icon metadata preserves current values

- **GIVEN** Explore or Commit KPI cards are composed from dashboard data
- **WHEN** optional icon metadata is present
- **THEN** labels, values, accents, and hints MUST remain unchanged from the current policy

### Product copy

- The UI MAY use recorte-oriented copy where it improves operator comprehension
- Existing constant names MAY remain stable even if their visible string values are updated

#### Scenario: renamed copy preserves behavior

- **GIVEN** the rail and home surfaces render product copy
- **WHEN** visible labels are updated for the polished shell
- **THEN** widget behavior and testable workflow semantics MUST remain unchanged
