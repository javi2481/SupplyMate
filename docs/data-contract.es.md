**Español** · [English](data-contract.md) · [README](../README.md) · [README ES](../README.es.md)

# Contrato de datos

Los CSVs en `data/` simulan una API externa partida por recurso. La clave primaria es **`product_id`** (código numérico del artículo).

## Recursos

| Recurso REST (simulado) | Archivo | Columnas principales |
|-------------------------|---------|----------------------|
| `GET /products` | `products.csv` | product_id, product_name, barcode(s), supplier, category, subcategory |
| `GET /prices` | `prices.csv` | product_id, price, price_offer, price_discount, pvp |
| `GET /inventory` | `inventory.csv` | product_id, current_stock, min_stock, max_stock, reorder_point |
| `GET /sales/summary` | `sales_summary.csv` | product_id, days, units_sold, period_end |
| `GET /replenishment-params` | `replenishment_params.csv` | product_id, lead_time_days, safety_stock |

Archivo adicional: `missions.csv` — aristas de complementos curadas para navegación guiada (opcional).

## Diagrama de relación

```text
product_id (PK)
    ├── products.csv      (identidad + taxonomía)
    ├── prices.csv        (comercial)
    ├── inventory.csv     (operativo)
    ├── sales_summary.csv (demanda 30d)
    └── replenishment_params.csv (lead time + safety)
```

## Regenerar desde el dump Excel

```bash
python scripts/export_catalog_csvs.py
```

Origen (local, no viene en git): `docs/perfumeria_enriched.xlsx` (~13.125 SKUs). El catálogo vivo en clones es `data/*.csv`.

## Runtime

- [`app/store.py`](../app/store.py) carga los CSVs al iniciar (cache in-memory).
- [`app/services/catalog_service.py`](../app/services/catalog_service.py) expone ficha unificada (`ProductMaster`) y recomendación determinística.
- Los campos min/max/reorder_point y precios son **contexto**; la cantidad a pedir usa la fórmula de 7 días en [`app/replenishment.py`](../app/replenishment.py).

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SUPPLYMATE_DATA_DIR` | `./data` | Directorio con los CSVs |
| `SUPPLYMATE_CATALOG_XLSX` | (vacío) | Opcional: cargar xlsx en lugar de CSVs |
