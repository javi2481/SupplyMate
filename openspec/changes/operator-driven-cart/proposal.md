# Proposal: Operator-driven cart (row add + order qty)

## Intent

The operator **builds** the purchase order **row by row**. Chat only **suggests** the current focus (recorte). In the SKU table, the operator types an order qty (field starts empty) and confirms with a cart icon. Revisar OC allows edits; **Exportar y terminar** downloads CSV and clears the cart.

This **supersedes** bulk “Agregar al pedido” (focus merge) and the auto-accumulate trigger in `chat-cart-oc`.

## Scope

### In Scope
- Chat success does not mutate the cart.
- Per-row add from SkuTable: empty qty input + `sug. N` + cart confirm; Tab between qty fields; Enter = confirm.
- Hide Cobertura / Prioridad columns to make room.
- `addLineToCart`: empty/0 no-op; upsert by `product_id` with typed `order_quantity` and Python `suggested_quantity`.
- Revisar OC editable; **Exportar y terminar** = CSV + clear cart + back to Explore.
- Footer / totals / CSV from `order_quantity`.

### Out of Scope
- NL qty, MOQ catalog, server cart API, multi-select checkboxes, replenishment formula changes.

## Success Criteria

- [ ] Chat turn leaves cart unchanged.
- [ ] Add two SKUs from different recortes via cart icon → both in OC.
- [ ] Empty/0 + cart does not add.
- [ ] Re-add same SKU updates order qty.
- [ ] Exportar y terminar exports and empties cart.
