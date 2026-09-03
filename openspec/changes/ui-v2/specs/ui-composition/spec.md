# Spec: ui-composition

## ADDED Requirements

### compose_next_step

- MUST accept `guidance`, `suggested_filters`, and `suggested_questions` without calling LLM or HTTP
- MUST place `GuidanceDecision` options/chips as `primary` when `action` is `ask_clarification` or `draft_oc` and a question or chips exist
- MUST place non-duplicate suggested filters in `secondary` (max 3, ranking order preserved)
- MUST place insight `suggested_questions` in `prompts` (tertiary). They MUST NOT be `primary`
- MUST drop a suggested filter whose `health_bucket` is already offered by a guidance chip (`add_health_bucket`)
- MUST drop a suggested filter whose label matches a guidance option (case-insensitive)
- GIVEN no guidance primary WHEN filters exist THEN the first filter MAY occupy `primary` and the rest stay `secondary`
- GIVEN `action=draft_oc` THEN primary MUST be the draft-OC chip (display label MAY be “Revisar compra”)

### explore_kpi_keys

- Live Explore strip MUST include at most: Productos (`skus`), Falta de stock (`understock`), Riesgo de quiebre (`stockout_risk`), Cobertura prom. (`avg_coverage`)
- MUST NOT include OC line count or estimated purchase value on the live Explore strip

### commit_kpi_keys

- Commit strip MUST include line count, unit sum, estimated value when present, and counts of `critical` / `high` priorities

### explore_table_columns

- Live Explore table column order MUST start: Prioridad, Producto, Pedir, Cobertura (días), Stock, Proveedor
- The former “Tendencia” header MUST be “Señal” and MUST reuse health-bucket `TREND_LABELS`
- SKU, Ritmo/día, Valor est., Estado MUST NOT be required in the default Explore column set

### chat_unfreeze_policy

- GIVEN `panel_mode=commit` and a `/chat` response `mode` in `list`/`explore`
  WHEN applying the response
  THEN the UI MUST NOT set `panel_mode` to explore or clear `frozen_scope` until the operator confirms
- GIVEN `panel_mode=explore` THEN list/explore chat MAY reset scope as today
