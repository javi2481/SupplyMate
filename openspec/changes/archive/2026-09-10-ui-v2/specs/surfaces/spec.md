# Spec: surfaces

## MODIFIED Requirements

### Live panel

- ONLY the current list-mode dashboard MUST use interactive charts (`on_select="rerun"`)
- Chat history MUST render dashboards without selection
- Live Explore MUST follow this visual order: compact scope, ≤4 KPIs, one Next Step heading combined with interactive category and coverage charts, remaining next-step chips that the charts do not cover, table, AI reading
- Category and coverage suggested-filter chips MUST NOT duplicate the charts when those charts have data; health, supplier, clarification, draft-OC, and insight prompts MAY remain as chips
- Live Commit MUST NOT render guidance chips, suggested filters, insight questions, or interactive charts
- Live Commit MUST render OC summary, priorities, export, and return-to-explore
- KPI density rules apply to the **live** panel only; the static history dashboard MAY keep its existing KPI row

### Navigation

- MUST show a compact scope line derived from active criteria (middle-dot separated, not a query-builder breadcrumb)
- Each active criterion MUST remain removable, or a single “limpiar” control MUST reset the scope
- MUST provide reset to empty scope in Explore
- Scope controls MUST be read-only in Commit

### Charts

- Category lollipop click MUST `add` category to scope and refresh slice (Explore only)
- Coverage histogram click MUST `add` bucket to scope (Explore only)
- Chart clicks MUST use `add`, never `toggle`

### Chips

- Clicking a next-step guidance chip MUST apply via `apply_guidance_chip` (same as today, including `draft_oc` → commit)
- Clicking a secondary suggested filter MUST `add` immediately (same as chart)
- Suggested filters MUST NOT render as a second first-class chip row when guidance primary exists
- Health and supplier filters MAY appear only as secondary next-step options (no new chart)

### Empty state

- GIVEN no live list session
  WHEN the app loads
  THEN MUST show a conversational home (prompt aligned with “¿Qué productos tengo que comprar?”) and MUST NOT show the live replenishment panel
- GIVEN slice with zero purchase_list items
  WHEN the live Explore panel renders
  THEN MUST show a fixed empty message and keep the compact scope line

### CSV

- Download MUST pass the same query params as the current (frozen) scope
- Button label MUST include count: `Exportar OC (N SKUs)`
- Export MUST remain commit-only

### SKU inspection

- Table row or `open_sku` option MUST set `highlight_product_id` and show “Cómo se calculó” without clearing the table

### Chrome

- Header MUST be product name + short tagline + mode state (Explorando / Revisando compra)
- Header MUST NOT teach Ask/Agent/Python/LLM vocabulary
- Analyst card title MUST be “Lectura del recorte” with caption “Generado por IA”
- Sidebar MUST NOT present non-clickable health ovals as if they were filters
- Chat input MUST stay reachable (sticky via `st.bottom` when the input is not at script root)
