# Delta for ui-composition

## MODIFIED Requirements

### Requirement: KPI card metadata

`KpiCard` MAY expose optional icon metadata for the presentation layer. Optional icon metadata MUST NOT be required by commit cards or existing tests unrelated to the visual shell. Live Explore KPI accents MUST be: Productos brand blue, Falta orange (health understock), Quiebre red (health stockout), Cobertura brand blue. The UI MUST NOT mutate the health or coverage color maps to achieve those accents.
(Previously: labels, values, accents, and hints MUST remain unchanged from the then-current policy.)

#### Scenario: KPI icon metadata preserves current values

- GIVEN Explore or Commit KPI cards are composed from dashboard data
- WHEN optional icon metadata is present
- THEN labels, values, and hints MUST remain unchanged from the current policy

#### Scenario: explore KPI accents

- GIVEN live Explore KPI cards
- WHEN accents are inspected
- THEN Productos and Cobertura MUST use brand blue
- AND Falta MUST use health understock orange
- AND Quiebre MUST use health stockout red
- AND the health and coverage color maps MUST be unchanged

### Requirement: Product copy

The UI MAY use recorte-oriented copy where it improves operator comprehension. Existing constant names MAY remain stable even if their visible string values are updated. The visible new-thread CTA copy MUST be `+ Nuevo recorte`.
(Previously: copy MAY change without locking the new-thread string.)

#### Scenario: renamed copy preserves behavior

- GIVEN the rail and home surfaces render product copy
- WHEN visible labels are updated for the native shell
- THEN widget behavior and testable workflow semantics MUST remain unchanged

#### Scenario: new-thread CTA copy

- GIVEN the sidebar new-thread control
- WHEN it renders
- THEN the visible label MUST be `+ Nuevo recorte`
