# Delta for react-adapter

## ADDED Requirements

### Requirement: Explore uses only the live catalog

Explore MUST render purchase rows and dashboard from FastAPI `/data`. It MUST NOT render Lovable `CATALOG` / `ROWS` / `compute()` / `answerFor()`.

#### Scenario: Slice fetch fails

- GIVEN the slice request fails
- WHEN Explore paints
- THEN the table MUST be empty
- AND chrome MUST say `Sin catálogo`
- AND MUST NOT say `Catálogo demo`
- AND MUST NOT show Pañales / Mamaderas demo SKUs

### Requirement: Chat drives the recorte

After a successful `/chat`, Explore MUST apply `ChatResponse.scope` and refetch the slice. It MUST NOT call `sliceFromText`.

#### Scenario: Operator types quiebre

- GIVEN a live catalog
- WHEN the operator sends `quiebre`
- THEN UiSlice health MUST follow Python `stockout_risk`
- AND the board MUST update from the new slice

### Requirement: Empty and missing copy

#### Scenario: Table search miss

- GIVEN no rows match the table search `X`
- THEN copy MUST include `No encontramos productos para “X”`

#### Scenario: Empty recorte

- GIVEN a loaded slice with zero table rows
- THEN copy MUST be `No hay productos en este recorte. Probá quitar un filtro.`

#### Scenario: Chart load failure

- GIVEN slice error and no category bars
- THEN copy MUST be `No pude cargar las categorías. Intentá de nuevo en un momento.`

## MODIFIED Requirements

### Requirement: Offline fallback hides API URL

The previous demo-catalog fallback is removed.

#### Scenario: API down

- GIVEN the slice fetch fails
- WHEN chrome shows status
- THEN it MUST say `Sin catálogo`
- AND MUST NOT display localhost / API host strings
- AND MUST NOT say Catálogo demo
