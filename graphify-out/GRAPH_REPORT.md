# Graph Report - SupplyMate  (2026-08-30)

## Corpus Check
- 110 files · ~26,515 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 717 nodes · 1568 edges · 55 communities (36 shown, 15 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 118 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `42697b72`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_tools.py
- AnalyticalScope
- get_replenishment_recommendation
- store.py
- models.py
- api.py
- bug_report.md
- test_api.py
- products.py
- streamlit_app.py
- export_catalog_csvs.py
- app/__init__.py
- supplymate
- graphify
- Traceability matrix — active changes
- SupplyMate
- panel_modes.py
- components.py
- README.md
- charts.py
- Requirements
- Tasks: engineering-quality
- Proposal: interactive-drilldown
- Protocolo de prueba beta — SupplyMate
- Design: interactive-drilldown
- Requirements
- Tasks: interactive-drilldown
- Plantilla — solicitud de cambio
- Design: engineering-quality
- Security spec (OWASP-minimal)
- Verify report — engineering-quality
- Política de mantenimiento — SupplyMate
- Proposal: engineering-quality
- Requirements
- Requirements
- Verify report — interactive-drilldown
- analyst.py
- Perfil operativo — rendimiento
- Proposal: llm-drilldown-insights
- Deployment spec
- Design: llm-drilldown-insights
- CI spec
- Traceability spec
- llm-drilldown-insights/tasks.md
- llm-drilldown-insights/verify-report.md
- smoke_api.sh script
- Agent
- date
- get
- Response
- asyncio

## God Nodes (most connected - your core abstractions)
1. `AnalyticalScope` - 82 edges
2. `ProductNotFoundError` - 29 edges
3. `run_analyze()` - 26 edges
4. `ProductMaster` - 25 edges
5. `run_supplymate()` - 23 edges
6. `PurchaseListItem` - 22 edges
7. `chat_dashboard()` - 22 edges
8. `CatalogStore` - 22 edges
9. `get_replenishment_recommendation()` - 21 edges
10. `InventoryDashboard` - 20 edges

## Surprising Connections (you probably didn't know these)
- `test_run_analyze_priorities_subset_of_purchase_list()` --uses--> `AnalyticalScope`  [INFERRED]
  tests/test_agent.py → app/models.py
- `_analyze_cache_key()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `_breadcrumb_labels()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `_effective_panel_scope()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py
- `fetch_analyze()` --uses--> `AnalyticalScope`  [INFERRED]
  ui/streamlit_app.py → app/models.py

## Import Cycles
- None detected.

## Communities (55 total, 15 thin omitted)

### Community 0 - "test_tools.py"
Cohesion: 0.14
Nodes (25): Any, _hydrate_context(), resolve_product(), get_inventory(), get_replenishment_params(), get_sales_history(), load_inventory(), load_replenishment_params() (+17 more)

### Community 1 - "AnalyticalScope"
Cohesion: 0.07
Nodes (70): AnalyticalScope, CategoryBar, CoverageBar, InteractionEvent, InventoryDashboard, PurchaseListItem, SuggestedFilter, chat_dashboard() (+62 more)

### Community 2 - "get_replenishment_recommendation"
Cohesion: 0.09
Nodes (34): ReplenishmentRecommendation, ReplenishmentResult, calculate_replenishment(), format_purchase_list_answer(), get_master(), get_replenishment_by_query(), get_replenishment_recommendation(), list_purchase_recommendations() (+26 more)

### Community 3 - "store.py"
Cohesion: 0.10
Nodes (32): ProductMaster, days_of_supply(), health_bucket(), _as_float(), _as_int(), _as_str(), _build_master(), CatalogStore (+24 more)

### Community 4 - "models.py"
Cohesion: 0.07
Nodes (72): Agent, build_commit_agent(), build_explain_agent(), build_insight_agent(), build_supply_agent(), _fallback_analyze_response(), get_model(), _parse_json_output() (+64 more)

### Community 5 - "api.py"
Cohesion: 0.05
Nodes (44): get_product(), get_replenishment(), health(), inventory_dashboard(), purchase_list(), purchase_list_csv(), Response, replenishment_slice() (+36 more)

### Community 6 - "bug_report.md"
Cohesion: 0.11
Nodes (16): Auditoría OSSTMM lite — Sección C (Internet), C — Seguridad en tecnologías de Internet, Fuera de alcance (OSSTMM D–F), Próximos pasos (producción), Actualización, Auditoría local, Dependencias y auditoría (OWASP A06), Pinning (+8 more)

### Community 8 - "products.py"
Cohesion: 0.08
Nodes (42): _extract_product_id(), build_classifier_agent(), classify_intent(), Agent, Intent, LLM concept router. None = classifier unavailable; caller should fall back., is_purchase_list_query(), is_top_categories_query() (+34 more)

### Community 9 - "streamlit_app.py"
Cohesion: 0.10
Nodes (42): add(), cache_key(), clear_highlight(), empty_scope(), Analytical scope: deterministic drill-down filters., remove(), reset(), scope_from_query_params() (+34 more)

### Community 10 - "export_catalog_csvs.py"
Cohesion: 0.48
Nodes (6): _as_num(), _as_str(), main(), Path, Split docs/perfumeria_enriched.xlsx into resource-oriented CSVs under data/.…, _write()

### Community 16 - "Traceability matrix — active changes"
Cohesion: 0.13
Nodes (15): dual-surface / metrics, dual-surface / purchase-export, dual-surface / surfaces (API-backed), engineering-quality / deployment, engineering-quality / security, interactive-drilldown / filter_rows, interactive-drilldown / scope, interactive-drilldown / slice-api (+7 more)

### Community 17 - "SupplyMate"
Cohesion: 0.13
Nodes (15): Alcance, Calidad y mantenimiento, Cómo funciona SupplyMate, Docker (API), Documentación / SDD, Flujo en terminal, Inicio rápido, Licencia (+7 more)

### Community 18 - "panel_modes.py"
Cohesion: 0.23
Nodes (11): can_export(), effective_scope(), PanelMode, Ask/Agent panel modes — pure helpers for explore vs commit., Filter dimensions (excluding highlight) must match when entering commit., scopes_match_filters(), validate_commit_request(), test_can_export_only_in_commit() (+3 more)

### Community 19 - "components.py"
Cohesion: 0.20
Nodes (7): DataFrame, build_purchase_dataframe(), _kpi_card(), Any, Componentes visuales didácticos para Streamlit., render_kpi_strip(), render_purchase_table()

### Community 20 - "README.md"
Cohesion: 0.21
Nodes (5): API (:8000), Matriz de compatibilidad, Navegador × SO (Streamlit :8501), No probado formalmente, Regresión manual sugerida

### Community 21 - "charts.py"
Cohesion: 0.22
Nodes (8): Chart, Scale, Tooltip, histogram(), lollipop(), _qty_color_scale(), Altair charts for SupplyMate drill-down (static + selectable)., Visual theme — colores semánticos para SupplyMate Operación.

### Community 22 - "Requirements"
Cohesion: 0.20
Nodes (9): Charts, Chips, CSV, Empty state, Live panel, Navigation, Requirements, SKU inspection (+1 more)

### Community 23 - "Tasks: engineering-quality"
Cohesion: 0.22
Nodes (8): Phase 0 — SDD, Phase 1 — Traceability audit, Phase 2 — Security (Strict TDD), Phase 3 — CI, Phase 4 — Smoke + performance, Phase 5 — Maintenance + audit docs, Phase 6 — UX + close, Tasks: engineering-quality

### Community 24 - "Proposal: interactive-drilldown"
Cohesion: 0.22
Nodes (8): Capabilities, Non-Goals, Proposal: interactive-drilldown, Risks, Roadmap (later changes, not this one), Rollback, What Changes, Why

### Community 25 - "Protocolo de prueba beta — SupplyMate"
Cohesion: 0.25
Nodes (8): Checklist UX automatizable (manual), Criterio de éxito beta, Duración, Escenario narrativo, Participante, Pasos, Protocolo de prueba beta — SupplyMate, Registro de hallazgos

### Community 26 - "Design: interactive-drilldown"
Cohesion: 0.25
Nodes (7): AnalyticalScope, Data path, Design: interactive-drilldown, Filter semantics, Gotcha, Principle, Streamlit

### Community 27 - "Requirements"
Cohesion: 0.25
Nodes (7): add, AnalyticalScope model, cache_key, filter_rows, remove and reset, Requirements, Spec: scope

### Community 28 - "Tasks: interactive-drilldown"
Cohesion: 0.25
Nodes (7): Phase 0 — SDD, Phase 1 — Scope + filter (Strict TDD), Phase 2 — Evidence + chips (Strict TDD), Phase 3 — API (Strict TDD), Phase 4 — Streamlit (verify), Phase 5 — Ship, Tasks: interactive-drilldown

### Community 29 - "Plantilla — solicitud de cambio"
Cohesion: 0.29
Nodes (7): 1. Resumen, 2. Motivación, 3. Impacto en el sistema, 4. Riesgos, 5. Plan de pruebas, 6. Decisión, Plantilla — solicitud de cambio

### Community 30 - "Design: engineering-quality"
Cohesion: 0.29
Nodes (6): CI layout, Design: engineering-quality, Environment, Performance thresholds, Security middleware stack, Traceability

### Community 31 - "Security spec (OWASP-minimal)"
Cohesion: 0.29
Nodes (6): Dependencies (A06), Error handling (A05), Headers, Input validation (A03), Rate limiting (A07), Security spec (OWASP-minimal)

### Community 32 - "Verify report — engineering-quality"
Cohesion: 0.29
Nodes (6): Coverage (critical modules), Spec coverage, TDD cycle evidence, UX / beta, Verdict, Verify report — engineering-quality

### Community 33 - "Política de mantenimiento — SupplyMate"
Cohesion: 0.33
Nodes (6): Evolución vs servicio, Flujo de cambio, Mantenimiento preventivo (Ley #2), Política de mantenimiento — SupplyMate, Referencias, Tipos de mantenimiento

### Community 34 - "Proposal: engineering-quality"
Cohesion: 0.33
Nodes (5): Non-Goals, Proposal: engineering-quality, Reference, What Changes, Why

### Community 35 - "Requirements"
Cohesion: 0.33
Nodes (5): Aligned endpoints, Data source, GET /replenishment/slice, Requirements, Spec: slice-api

### Community 36 - "Requirements"
Cohesion: 0.33
Nodes (5): Ranking order (first applicable, up to 3), Requirements, Spec: suggested-filters, suggest_next_filters, SuggestedFilter shape

### Community 37 - "Verify report — interactive-drilldown"
Cohesion: 0.33
Nodes (6): Spec coverage, TDD cycle evidence, Traceability, UX checklist (5 min manual), Verdict, Verify report — interactive-drilldown

### Community 39 - "Perfil operativo — rendimiento"
Cohesion: 0.40
Nodes (4): Mix de carga esperado (MVP), Notas, Perfil operativo — rendimiento, Umbrales smoke (`tests/test_performance.py`)

### Community 40 - "Proposal: llm-drilldown-insights"
Cohesion: 0.40
Nodes (4): Non-Goals, Proposal: llm-drilldown-insights, What Changes, Why

### Community 41 - "Deployment spec"
Cohesion: 0.50
Nodes (3): Deployment spec, Docker, Smoke script

### Community 42 - "Design: llm-drilldown-insights"
Cohesion: 0.50
Nodes (3): Ask / Agent, Design: llm-drilldown-insights, Flow

## Knowledge Gaps
- **148 isolated node(s):** `Descripción`, `Pasos para reproducir`, `Comportamiento esperado`, `Comportamiento actual`, `Entorno` (+143 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 281 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AnalyticalScope` connect `AnalyticalScope` to `get_replenishment_recommendation`, `models.py`, `api.py`, `streamlit_app.py`, `panel_modes.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `ProductNotFoundError` connect `models.py` to `test_tools.py`, `AnalyticalScope`, `get_replenishment_recommendation`, `store.py`, `api.py`, `test_api.py`, `products.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `ProductMaster` connect `store.py` to `AnalyticalScope`, `get_replenishment_recommendation`, `models.py`, `api.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `AnalyticalScope` (e.g. with `inventory_dashboard()` and `purchase_list()`) actually correct?**
  _`AnalyticalScope` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ProductNotFoundError` (e.g. with `chat()` and `get_product()`) actually correct?**
  _`ProductNotFoundError` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `run_analyze()` (e.g. with `AnalyzeRequest` and `CommitSummary`) actually correct?**
  _`run_analyze()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ProductMaster` (e.g. with `get_product()` and `get_master()`) actually correct?**
  _`ProductMaster` has 6 INFERRED edges - model-reasoned connections that need verification._