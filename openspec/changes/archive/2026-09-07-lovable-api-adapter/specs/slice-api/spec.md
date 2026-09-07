# Spec: slice-api (delta — TypeScript client)

## ADDED Requirements

### Requirement: ScopeQuery serializes full AnalyticalScope query params

The React FastAPI client MUST serialize repeatable query params that match
FastAPI `_scope_dependency`: `category`, `subcategory`, `coverage_bucket`,
`health_bucket`, `supplier`, `name_token`, `highlight_product_id`, and `limit`.

#### Scenario: Coverage bucket with canonical en-dash label

- **GIVEN** a UI scope with coverage band `"0–3 días"`
- **WHEN** `toSearchParams` / `fetchSlice` builds the URL
- **THEN** the query MUST include `coverage_bucket=0–3 días` (Unicode en-dash)
- **AND** MUST NOT use ASCII hyphen-only `"0-3"`

#### Scenario: Multiple dimensions AND across axes

- **GIVEN** categories `["Pañales"]` and health buckets `["stockout_risk"]`
- **WHEN** the slice URL is built
- **THEN** both `category` and `health_bucket` MUST appear as query params

### Requirement: Product id path encoding

`GET /products/{id}/replenishment` MUST encode the path segment with
`encodeURIComponent`.

#### Scenario: Special characters in product id

- **GIVEN** a product_id containing reserved URL characters
- **WHEN** `fetchReplenishment` is called
- **THEN** the request path MUST be percent-encoded
