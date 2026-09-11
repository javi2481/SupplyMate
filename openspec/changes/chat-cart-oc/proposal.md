# Proposal: Chat cart → OC (multi-rubro)

## Intent

The chat thread is the operator’s **order cart**, not a single-rubro recorte. Successful purchase turns accumulate SKUs across categories; Armar OC / Revisar OC / CSV export that cart. Explore still shows **current focus** (last purchase turn). Python quantities remain the only numbers.

## Scope

### In Scope
- Thread-scoped cart (`CartLine[]`) persisted with the panel. New thread / delete last → empty cart.
- Add only on successful purchase turns with non-empty `purchase_list` and mode explore/list/single (not sales).
- Merge by `product_id`; duplicate SKU keeps **max** `recommended_quantity` (never sum).
- Refinement: drop cart lines that share any category with the new items, then add the new lines.
- OC from cart if non-empty, else current focus purchase list. CSV from cart client-side when the cart is the source (multi-rubro without a new API).
- Chat footer: `En el pedido: N líneas · X u.` when the cart is non-empty.

### Out of Scope
- Runner / routing changes, missions.csv, pairwise eval harness, server multi-category CSV, LLM-authored quantities.

## Capabilities

### New Capabilities
- `chat-cart`: Thread cart merge, totals, OC/CSV projection.

### Modified Capabilities
- `react-adapter`: `send` / `openPo` / export / footer read the thread cart.

## Affected Areas

- `frontend/src/lib/chatTurn.ts`, `frontend/src/lib/cart.ts` (helpers)
- `frontend/src/routes/index.tsx`
- Vitest: `cart.test.ts`, `chatTurn.test.ts`

## Risks

- Refinement by primary category can drop sibling SKUs in that category that were added by an earlier unrelated turn (accepted MVP).
- Client CSV omits server-only columns; focus-only export still uses `/replenishment/purchase-list.csv`.
- `relation` comes from `trace.interpretation.relation`; missing trace defaults to `new_query` (max-merge).

## Rollback Plan

Revert the change. Threads without `cart` load as empty via `panelOf`.

## Success Criteria

- [ ] Two purchase turns in different categories → OC lists both; same SKU twice → max qty.
- [ ] Refinement of a group replaces that group’s cart lines; other categories remain.
- [ ] Sales / empty `purchase_list` do not add. New thread has an empty cart.
- [ ] Footer shows line/unit counts from the cart.
