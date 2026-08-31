# Design: interactive-drilldown

## Principle

**LLM only on free-text `POST /chat`.** Python calculates, filters, ranks next filters, exports.

```text
POST /chat          → classify + root list (once)
GET /slice          → filter + evidence + chips (every click/chip)
GET /purchase-list.csv?… → same scope as slice
GET /products/{id}/replenishment → SKU detail (existing)
```

## AnalyticalScope

```python
class AnalyticalScope(BaseModel):
    categories: list[str] = []
    coverage_buckets: list[str] = []
    health_buckets: list[str] = []
    suppliers: list[str] = []
    highlight_product_id: str = ""
```

- Empty scope = full inventory (root).
- **add** is idempotent (click/chip). **remove** = breadcrumb ×. **reset** = clear all.
- Limits: categories/coverage_buckets/suppliers ≤ 5; health_buckets ≤ 4; excess ignored.
- **cache_key**: sorted lists + `SALES_AS_OF`; order-independent.

## Filter semantics

- Within one dimension: OR (e.g. two categories).
- Across dimensions: AND (category + coverage bucket).
- `highlight_product_id` does not filter rows; opens “Cómo se calculó” only.
- Impossible criteria → 0 rows, 200, empty evidence text.

## Data path

```text
_sku_rows_cache (all SKUs, formula once)
    → filter_rows(scope)
    → from_rows / purchase_items
    → suggest_next_filters
```

No `calculate_replenishment` per click.

## Streamlit

- **Live panel**: last list-mode response; charts with `on_select="rerun"`.
- **History**: static render (no selection).
- Breadcrumb + “Limpiar filtros”.
- CSV button: `Exportar OC (N SKUs)`.

## Gotcha

`on_select` selection survives reruns. Never toggle on chart event; only add. Compare to last applied selection if needed.
