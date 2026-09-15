# react-adapter (delta)

## Requirements

### Requirement: SkuTable per-row order entry
The SKU table MUST NOT show Cobertura or Prioridad columns. **A pedir** MUST be an empty editable field with suggested qty visible (`sug. N`). A cart control per row MUST confirm add. Tab MUST move between qty inputs. Enter MUST confirm the focused row. Bulk **Agregar al pedido** MUST NOT appear on the recorte toolbar.

### Requirement: Revisar OC editable and finish
When the OC is cart-backed, lines MUST allow editing `order_quantity` and removal. **Exportar y terminar** MUST export the cart CSV, clear the cart, and return to Explore.
