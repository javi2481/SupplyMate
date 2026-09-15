# chat-cart (delta)

## Requirements

### Requirement: Chat turns MUST NOT auto-add to the cart
Chat success with a non-empty `purchase_list` MUST leave the thread cart unchanged.

### Requirement: Lines enter the cart only via per-row confirm
`addLineToCart` MUST add or upsert a single SKU when given a valid integer order qty ≥ 1. Empty, 0, non-integer, or out-of-range MUST be a no-op. Upsert MUST set `order_quantity` to the confirmed qty and refresh `suggested_quantity` from the row’s Python recommendation.

### Requirement: order_quantity drives totals and export
`cartTotals`, footer, OC units/value, and client CSV MUST use `order_quantity` (value scaled from suggested). CSV MUST include `order_quantity` and `suggested_quantity`.

### Requirement: Export and finish clears the cart
After a successful cart CSV export via **Exportar y terminar**, the thread cart MUST be empty.
