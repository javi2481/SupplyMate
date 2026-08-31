# Deployment spec

## Smoke script

Given API at `SUPPLYMATE_API_URL` (default `http://127.0.0.1:8000`):

- **WHEN** `GET /health` **THEN** status 200 and `{"status":"ok"}`
- **WHEN** `GET /replenishment/slice?limit=3` **THEN** status 200 with keys `scope`, `evidence`, `dashboard`, `purchase_list`, `suggested_filters`
- **WHEN** `GET /replenishment/purchase-list.csv?limit=5` **THEN** status 200 and non-empty CSV body
- **WHEN** `GET /products/6033436/replenishment` **THEN** status 200 and `recommended_quantity` equals 172

## Docker

- `docker build` MUST succeed with root `Dockerfile`
- Container MUST pass smoke script when started on port 8000
