# Design: Answer Surface Continuity

## Principle

**One AnalyticalScope, one Answer Surface.** Navigation, KPIs, charts, and SKU detail all mutate or reflect the same session scope. History is UI session state — not an API concern.

```text
click / chip / KPI / chat refine
  → push current scope (if dump changed)
  → mutate (add / strip / set_highlight)
  → _set_scope + invalidate slice by cache_key
  → slot: charts XOR SKU card

Volver → pop → _set_scope (no push) → refetch
Limpiar / Nuevo recorte → clear history + reset scope
```

## Scope history

Module: `app/services/scoping/history.py` (Streamlit-free), re-exported via `app.services.scope`.

| Op | Behavior |
|----|----------|
| `push(history, scope)` | No-op if dump equals top; cap 20 (drop oldest) |
| `pop(history)` | `(AnalyticalScope, remaining)` or `None` |
| `clear()` | `[]` |
| `loads(raw)` | Validate each entry with Pydantic; drop invalid |

Persisted in `SNAPSHOT_KEYS` as `scope_history`. Not part of `AnalyticalScope`, `POST /chat`, or `GET /slice`.

All Explore mutations go through `_commit_scope(new, *, push=True)`. Volver uses `push=False`. Commit mode’s “Volver a explorar” is unchanged and does not clear Explore history.

## Context bar

Show when filters OR history non-empty OR highlight set:

`[← Volver]  Cosmética  [Limpiar]` + existing SKU count caption.

Volver visible but disabled when stack empty. Copy: `VOLVER_SCOPE = "Volver"` (distinct from `BACK_TO_EXPLORE`).

Do not revive dead `render_breadcrumb`.

## KPI controls

| Control | Mutation |
|---------|----------|
| Productos | Strip health/coverage/tokens/highlight; keep categories (+ subcategories). No-op if already clean/root |
| Falta de stock | `add(health_bucket, understock)` |
| Riesgo | `add(health_bucket, stockout_risk)` |
| Cobertura | Not a filter button; histogram already `add(coverage_bucket)` |

Policy as pure functions (unit-tested). Render count KPIs as Streamlit buttons; Cobertura stays non-button KPI chrome.

## SKU slot

When `highlight_product_id` + `highlight_calc`: hide inventory KPIs and charts; show product card (Comprar N, stock/demand/ROP, closed “Cómo se calculó”). Chat turn: compact line only — no duplicate `format_single_product_answer` under the expander.

`mode=single`: keep `live_list_active`; push; set_highlight; fetch calc; rerun panel. If no live session, open Explore with highlight on empty or API scope.

## Charts

Lollipop: encode stroke width and point size by `_selected`; keep brand blue. Histogram: `mark_text` with `sku_count`; bar color unchanged.

## Security

- History from disk via `loads` / Pydantic only
- Cap 20; no free-text KPI values; SKU id from API/chip
- No clickable HTML KPIs; escape product names in markdown
- Zero new endpoints
