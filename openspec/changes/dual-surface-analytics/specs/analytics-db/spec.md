# Spec: analytics-db

> **Superseded:** `scripts/build_analytics_db.py` and DuckDB are gone.
> Dashboard aggregates run in Python (`app/services/analytics/dashboard.py`) on the catalog store.

## Purpose

## Purpose

Provide a regenerable DuckDB warehouse for Superset without duplicating the replenishment formula in SQL.

## Requirements

### Build

- GIVEN resource CSVs under `data/`
  WHEN `scripts/build_analytics_db.py` runs
  THEN it MUST write `data/supplymate.duckdb` containing base tables and `analytics_sku`

### Materialization

- GIVEN each SKU in the catalog
  WHEN `analytics_sku` is built
  THEN `recommended_quantity` MUST match `calculate_replenishment` for that SKU
- The DuckDB schema MUST NOT recompute recommended quantity via an alternate SQL formula

### Health view

- GIVEN materialized `analytics_sku`
  THEN a view `v_inventory_health` MUST expose bucket counts and average Coverage where defined

### Regeneration

- The DuckDB file MAY be gitignored
- Users MUST be able to regenerate it with a documented command
