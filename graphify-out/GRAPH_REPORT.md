# Graph Report - SupplyMate  (2026-08-30)

## Corpus Check
- 54 files · ~13,909 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 285 nodes · 775 edges · 16 communities (11 shown, 3 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c1b2dc47`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- agent.py
- dashboard.py
- catalog_service.py
- store.py
- models.py
- ProductMaster
- classify_intent
- ProductNotFoundError
- products.py
- streamlit_app.py
- export_catalog_csvs.py
- app/__init__.py
- supplymate
- graphify

## God Nodes (most connected - your core abstractions)
1. `ProductNotFoundError` - 29 edges
2. `ProductMaster` - 25 edges
3. `run_supplymate()` - 23 edges
4. `CatalogStore` - 22 edges
5. `get_replenishment_recommendation()` - 21 edges
6. `resolve_product_id()` - 20 edges
7. `get_store()` - 20 edges
8. `calculate_replenishment()` - 17 edges
9. `resolve_from_message()` - 15 edges
10. `ChatResponse` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_run_supplymate_quantity_matches_python_calc()` --uses--> `ChatResponse`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_llm_unknown_does_not_force_a_random_sku()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_run_supplymate_unknown_product()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_replenishment_unknown()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_catalog_service.py → app/models.py
- `test_load_inventory_unknown_product()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_tools.py → app/models.py

## Import Cycles
- None detected.

## Communities (16 total, 3 thin omitted)

### Community 0 - "agent.py"
Cohesion: 0.10
Nodes (37): Any, build_explain_agent(), build_supply_agent(), get_model(), _hydrate_context(), Agent, _run_purchase_list(), _run_single_product() (+29 more)

### Community 1 - "dashboard.py"
Cohesion: 0.20
Nodes (16): CategoryBar, CategorySalesBar, CoverageBar, InventoryDashboard, coverage_bucket(), from_rows(), Inventory dashboard for the Streamlit chat — same metrics as Python…, total_recommended_qty() (+8 more)

### Community 2 - "catalog_service.py"
Cohesion: 0.10
Nodes (40): purchase_list(), PurchaseListItem, ReplenishmentRecommendation, Resolve free-text to product_id: catalog code, barcode, or name., resolve_product_id(), calculate_replenishment(), chat_dashboard(), format_dashboard_answer() (+32 more)

### Community 3 - "store.py"
Cohesion: 0.16
Nodes (19): ProductSearchHit, _as_float(), _as_int(), _as_str(), _build_master(), CatalogStore, _expand_sales(), _index_barcodes() (+11 more)

### Community 4 - "models.py"
Cohesion: 0.22
Nodes (19): Route by concept, then let deterministic Python compute numbers. 1. Regex fast-…, run_supplymate(), Inventory, ReplenishmentParams, SaleRecord, SalesHistory, SupplyContext, asyncio (+11 more)

### Community 5 - "ProductMaster"
Cohesion: 0.19
Nodes (18): ProductMaster, ReplenishmentResult, analytics_rows(), days_of_supply(), health_bucket(), Shared analytics metrics — canonical labels for Operation + Analytics., sku_analytics_row(), computed_field (+10 more)

### Community 6 - "classify_intent"
Cohesion: 0.23
Nodes (11): build_classifier_agent(), classify_intent(), Agent, Intent, LLM concept router. None = classifier unavailable; caller should fall back., parse_intent_label(), Intent, Extract a single intent label from noisy LLM output. (+3 more)

### Community 7 - "ProductNotFoundError"
Cohesion: 0.09
Nodes (18): chat(), get_product(), get_replenishment(), health(), inventory_dashboard(), purchase_list_csv(), search_products(), ChatRequest (+10 more)

### Community 8 - "products.py"
Cohesion: 0.12
Nodes (28): _extract_product_id(), is_purchase_list_query(), is_top_categories_query(), match_rule_intent(), _normalize(), True when the user asks for a replenishment list or inventory dashboard., Cheap regex router. None means the concept was not recognized., clear_product_caches() (+20 more)

### Community 9 - "streamlit_app.py"
Cohesion: 0.22
Nodes (11): Chart, Tooltip, _histogram(), _lollipop(), SupplyMate · Operación — Streamlit assistant (FastAPI /chat + OC export)., Ranking: one categoric + one numeric → lollipop (data-to-viz)., Numeric distribution → histogram (ordered bins on X, counts on Y)., render_calculation() (+3 more)

### Community 10 - "export_catalog_csvs.py"
Cohesion: 0.48
Nodes (6): _as_num(), _as_str(), main(), Path, Split docs/perfumeria_enriched.xlsx into resource-oriented CSVs under data/.…, _write()

## Knowledge Gaps
- **2 isolated node(s):** `C:\Users\Equipo\.local\bin\graphify.exe`, `supplymate`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 62 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ProductNotFoundError` connect `ProductNotFoundError` to `agent.py`, `catalog_service.py`, `store.py`, `models.py`, `products.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `ProductMaster` connect `ProductMaster` to `dashboard.py`, `catalog_service.py`, `store.py`, `models.py`, `ProductNotFoundError`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `classify_intent()` connect `classify_intent` to `agent.py`, `models.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `ProductNotFoundError` (e.g. with `chat()` and `get_product()`) actually correct?**
  _`ProductNotFoundError` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ProductMaster` (e.g. with `get_product()` and `get_master()`) actually correct?**
  _`ProductMaster` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `CatalogStore` (e.g. with `Inventory` and `ProductMaster`) actually correct?**
  _`CatalogStore` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `C:\Users\Equipo\.local\bin\graphify.exe`, `supplymate` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._