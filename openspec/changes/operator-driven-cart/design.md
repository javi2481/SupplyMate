# Design: Operator-driven cart (row add)

## Flow

1. Chat updates Explore focus only.
2. Operator types qty in SkuTable **A pedir** (starts empty) and confirms with cart / Enter → `addLineToCart`.
3. Across recortes, lines accumulate in the thread cart.
4. Revisar OC edits / removes lines.
5. **Exportar y terminar** → CSV + `emptyCart()` + Explorar.

## CartLine

| Field | Role |
|-------|------|
| `suggested_quantity` | Python `recommended_quantity` at add time |
| `order_quantity` | Operator-typed qty at confirm (or later OC edit) |
| `estimated_purchase_value` | Value at suggested; totals scale by order/suggested |

## addLineToCart

- `clampOrderQuantity` must be integer 1..1e6; else cart unchanged.
- Upsert by `product_id`: replace metadata + suggested from row; set `order_quantity` to typed value (always overwrite on explicit confirm).
- No bulk `addFocusToCart` in the UI path.

## SkuTable UX

- Columns: product, stock, sales 30d, A pedir (input + sug), cart, salud, detalle. No Cobertura / Prioridad.
- Tab order: only qty inputs. Cart and chevron `tabIndex={-1}`.
- Click sug copies suggested into the input.
- stopPropagation on input/cart so drawer does not open.
- Rows already in cart show a short “En el pedido” cue.

## Validation

- Integers 1..1e6 for add and OC edit.
- Remove line = filter by `product_id`.
