# Spec: surfaces

## Requirements

### Live panel

- ONLY the current list-mode dashboard MUST use interactive charts (`on_select="rerun"`)
- Chat history MUST render dashboards without selection

### Navigation

- MUST show breadcrumb derived from scope (Inventario › …)
- Each active criterion MUST be removable (×)
- MUST provide “Limpiar filtros” / reset to empty scope

### Charts

- Category lollipop click MUST `add` category to scope and refresh slice
- Coverage histogram click MUST `add` bucket to scope
- Chart clicks MUST use `add`, never `toggle`

### Chips

- Clicking a suggested filter MUST `add` immediately (same as chart)
- Health and supplier filters MAY appear only as chips (no new chart)

### Empty state

- GIVEN slice with zero purchase_list items
  WHEN panel renders
  THEN MUST show fixed empty message and keep breadcrumb

### CSV

- Download MUST pass same query params as current scope
- Button label MUST include count: `Exportar OC (N SKUs)`

### SKU inspection

- Table row or `open_sku` chip MUST set `highlight_product_id` and show “Cómo se calculó” without clearing the table
