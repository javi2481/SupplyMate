# Design: lovable-api-adapter

## Principle

**UI presents; Python decides.** Components receive projected rows. No
`compute()` on the happy path when FastAPI is up.

```text
React components
    → SkuListRow (projection)
    → useScope / useSlice
    → api.ts (ScopeQuery)
    → FastAPI GET /replenishment/slice | POST /chat | GET /products/{id}/replenishment
    → CatalogStore + calculate_replenishment
```

## Scope serialization

`ScopeQuery` MUST mirror `_scope_dependency` query params:

| Query param | AnalyticalScope field |
|-------------|----------------------|
| `category` | `categories` |
| `subcategory` | `subcategories` |
| `coverage_bucket` | `coverage_buckets` |
| `health_bucket` | `health_buckets` |
| `supplier` | `suppliers` |
| `name_token` | `name_tokens` |
| `highlight_product_id` | `highlight_product_id` |
| `limit` | (pagination only) |

`guidance_dismissed` is out of scope for this UI.

### Coverage bands (canonical)

Copy `COVERAGE_ORDER` from `app/services/analytics/dashboard.py`:

```text
"0–3 días" | "3–7 días" | "7–14 días" | "14–30 días" | "30+ días"
```

UI chips MUST send these exact strings (en-dash U+2013).

### Health mapping

| UI tag | API health_bucket | Notes |
|--------|-------------------|-------|
| `riesgo_quiebre` | `stockout_risk` | |
| `sobrestock` | `overstock` | |
| `sin_stock` | — | Client filter: `current_stock === 0` |
| (understock KPI) | `understock` | Label: "Falta de stock" |

### Priority mapping

| API `operational_priority` | Label |
|----------------------------|-------|
| `critical` | Crítica |
| `high` | Alta |
| `normal` | Normal |

Do not collapse `critical` and `high`. Do not invent Media/Baja.

## Adapter

`PurchaseListItem` → `SkuListRow` is a **visual projection** only:

- stock, qty, coverage days, priority label, health tags from `health_bucket` + stock
- MUST NOT invent `demand_horizon`, `lead_time_days`, `safety_stock` for the table
- SKU drawer loads `GET /products/{id}/replenishment` for calculation facts

## Offline fallback

If `VITE_SUPPLYMATE_API_URL` is unset/empty **or** fetch fails:

- Use demo catalog (`supplymate.ts` mock)
- Status chip: "Catálogo demo"
- NEVER show API host/URL in product chrome

## Etapa gates

1. **A.5** — client + adapter + tests; UI still mock-driven (except 5 coverage chips)
2. **Freeze** — no shell redesign from Lovable
3. **B** — wire `useQuery` / chat / drawer / CSV; mock only as fallback
