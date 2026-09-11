# Spec: chat-scope-apply

## Requirements

### Requirement: Chat success replaces the recorte from Python scope

`applyChatScope` MUST map `ChatResponse.scope` onto `UiSlice` with replace semantics. It MUST NOT parse the operator message for filters.

#### Scenario: Inventory risk

- **GIVEN** a successful chat with `health_buckets: ["stockout_risk"]` and empty categories
- **WHEN** the mapper runs on a UiSlice that had category Cuidado
- **THEN** health MUST be `riesgo_quiebre` and cats MUST be empty

#### Scenario: List mode

- **GIVEN** `mode` is `list` and a scope payload
- **WHEN** the mapper runs
- **THEN** `buyOnly` MUST be true

#### Scenario: Null scope

- **GIVEN** `scope` is null and a current UiSlice
- **WHEN** the mapper runs
- **THEN** the current UiSlice MUST be unchanged except optional product open

### Requirement: Operator copy for chat failure

#### Scenario: Not found

- **GIVEN** HTTP 404
- **WHEN** formatting the assistant message for query `SKU999`
- **THEN** the text MUST be `No encontré «SKU999» en el catálogo.`
- **AND** MUST NOT include Product not found / demo SKU names

#### Scenario: Catalog did not load

- **GIVEN** a network or 5xx failure
- **WHEN** formatting the assistant message
- **THEN** the text MUST be `No pude cargar el catálogo. Intentá de nuevo en un momento.`
- **AND** MUST NOT mention motor, API, or localhost
