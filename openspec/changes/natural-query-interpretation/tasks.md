# Tasks: natural-query-interpretation

## Phase 0 — SDD

- [ ] 0.1 tasks.md (this file)
- [ ] 0.2 Remove incomplete stub `app/category_resolve.py`

## Phase 1 — Un grupo + scope en chat (MVP)

- [ ] 1.1 Models: QueryInterpretation, ResolvedReference, ChatResponse extensions, AnalyticalScope.subcategories
- [ ] 1.2 Scope/filters: scope.py, dashboard.filter_rows, API subcategory param, Streamlit scope_query_params + breadcrumb
- [ ] 1.3 Modules: query_interpretation.py, reference_resolver.py, scope_builder.py, explore_answer.py
- [ ] 1.4 Router: run_supplymate reorder + _run_explore
- [ ] 1.5 Streamlit: apply scope from chat; mode explore/disambiguation
- [ ] 1.6 Tests: golden_reference_resolution.csv, test_reference_resolver, test_api jabones

## Phase 2 — Multi-grupo comparativo

- [ ] 2.1 Multi-reference interpret_query + SupplyMateQueryInterpreter (LLM JSON)
- [ ] 2.2 OR category+subcategory in filter_rows; GroupSummary per reference
- [ ] 2.3 golden_query_interpretation.csv; test jabones + shampoo

## Phase 3 — inventory_risk sobre grupos

- [ ] 3.1 filter_hints → health_buckets in build_scope
- [ ] 3.2 Router inventory_risk path
- [ ] 3.3 Tests riesgo + jabones

## Phase 4 — Desambiguación

- [ ] 4.1 blocking ResolutionResult + mode=disambiguation
- [ ] 4.2 Streamlit disambiguation UI
- [ ] 4.3 Deprecate legacy 4-intent classifier where covered

## Verify

- [ ] verify-report.md
- [ ] pytest CI set green
- [ ] graphify update
