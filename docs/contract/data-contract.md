**English** · [Español](data-contract.es.md) · [README](../README.md) · [README ES](../README.es.md)

# Data contract

CSVs in `data/` simulate an external API split by resource. Primary key is **`product_id`** (numeric article code).

## Resources

| Simulated REST resource | File | Main columns |
|-------------------------|------|--------------|
| `GET /products` | `products.csv` | product_id, product_name, barcode(s), supplier, category, subcategory |
| `GET /prices` | `prices.csv` | product_id, price, price_offer, price_discount, pvp |
| `GET /inventory` | `inventory.csv` | product_id, current_stock, min_stock, max_stock, reorder_point |
| `GET /sales/summary` | `sales_summary.csv` | product_id, days, units_sold, period_end |
| `GET /replenishment-params` | `replenishment_params.csv` | product_id, lead_time_days, safety_stock |

Additional file: `missions.csv` — curated complement edges for guided navigation (optional).

## Relationship diagram

```text
product_id (PK)
    ├── products.csv      (identity + taxonomy)
    ├── prices.csv        (commercial)
    ├── inventory.csv     (operational)
    ├── sales_summary.csv (30d demand)
    └── replenishment_params.csv (lead time + safety)
```

## Regenerate from Excel dump

```bash
python scripts/export_catalog_csvs.py
```

Source (local, not shipped in git): `docs/perfumeria_enriched.xlsx` (~13,125 SKUs). The live catalog in clones is `data/*.csv`.

## Runtime

- [`app/store.py`](../app/store.py) loads CSVs at startup (in-memory cache).
- [`app/services/analytics/catalog_service.py`](../app/services/analytics/catalog_service.py) exposes unified row (`ProductMaster`) and deterministic recommendation.
- Fields min/max/reorder_point and prices are **context**; order quantity uses the 7-day formula in [`app/core/replenishment.py`](../app/core/replenishment.py).

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPPLYMATE_DATA_DIR` | `./data` | Directory containing CSVs |
| `SUPPLYMATE_CATALOG_XLSX` | (empty) | Optional: load xlsx instead of CSVs |
