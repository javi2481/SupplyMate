# Tasks: natural-query-interpretation

## Phase 0 — SDD

- [x] 0.1 tasks.md (this file)
- [x] 0.2 Remove incomplete stub `app/category_resolve.py`

## Phase 1 — Un grupo + scope en chat (MVP)

- [x] 1.1 Models: QueryInterpretation, ResolvedReference, ChatResponse extensions, AnalyticalScope.subcategories
- [x] 1.2 Scope/filters: scope.py, dashboard.filter_rows, API subcategory param, Streamlit scope_query_params + breadcrumb
- [x] 1.3 Modules: query_interpretation.py, reference_resolver.py, scope_builder.py, explore_answer.py
- [x] 1.4 Router: run_supplymate reorder + _run_explore
- [x] 1.5 Streamlit: apply scope from chat; mode explore/disambiguation
- [x] 1.6 Tests: golden_reference_resolution.csv, test_reference_resolver, test_api jabones

## Phase 2 — Multi-grupo comparativo

- [x] 2.1 Multi-reference interpret_query + SupplyMateQueryInterpreter (LLM JSON)
- [x] 2.2 OR category+subcategory in filter_rows; GroupSummary per reference
- [x] 2.3 golden_query_interpretation.csv; test jabones + shampoo

## Phase 3 — inventory_risk sobre grupos

- [x] 3.1 filter_hints → health_buckets in build_scope
- [x] 3.2 Router inventory_risk path
- [x] 3.3 Tests riesgo + jabones

## Phase 4 — Desambiguación

- [x] 4.1 blocking ResolutionResult + mode=disambiguation
- [x] 4.2 Streamlit disambiguation UI (option buttons)
- [x] 4.3 Legacy 4-intent classifier retained as fallback for unknown paraphrases

## Verify

- [x] verify-report.md
- [x] pytest CI set green (185 passed, not llm)
- [x] graphify update
