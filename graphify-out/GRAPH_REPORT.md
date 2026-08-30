# Graph Report - SupplyMate  (2026-08-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 282 nodes · 773 edges · 15 communities (11 shown, 2 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9250b86c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 13

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
- `test_llm_unknown_does_not_force_a_random_sku()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_run_supplymate_unknown_product()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_agent.py → app/models.py
- `test_replenishment_unknown()` --uses--> `ProductNotFoundError`  [INFERRED]
  tests/test_catalog_service.py → app/models.py
- `test_resolve_from_message_by_code()` --calls--> `resolve_from_message()`  [EXTRACTED]
  tests/test_tools.py → app/products.py
- `test_search_products()` --calls--> `search_products()`  [EXTRACTED]
  tests/test_catalog_service.py → app/services/catalog_service.py

## Import Cycles
- None detected.

## Communities (15 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (43): Any, build_explain_agent(), build_supply_agent(), _extract_product_id(), get_model(), _hydrate_context(), Agent, _run_single_product() (+35 more)

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (37): _run_purchase_list(), get_product(), get_replenishment(), health(), inventory_dashboard(), purchase_list(), purchase_list_csv(), search_products() (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (36): load_products(), Path, Resolve free-text to product_id: catalog code, barcode, or name., resolve_product_id(), calculate_replenishment(), format_purchase_list_answer(), format_sales_answer(), get_master() (+28 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (18): _as_float(), _as_int(), _as_str(), _build_master(), CatalogStore, _expand_sales(), _index_barcodes(), load_store_from_csvs() (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.20
Nodes (22): Route by concept, then let deterministic Python compute numbers. 1. Regex fast-…, run_supplymate(), _run_top_categories(), chat(), ChatResponse, Inventory, ReplenishmentParams, SaleRecord (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (18): ProductMaster, ReplenishmentResult, analytics_rows(), days_of_supply(), health_bucket(), Shared analytics metrics — canonical labels for Operation + Analytics., sku_analytics_row(), computed_field (+10 more)

### Community 6 - "Community 6"
Cohesion: 0.16
Nodes (18): ProductNotFoundError, load_inventory(), load_replenishment_params(), load_sales_history(), date, Path, Exception, test_chat_not_found() (+10 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (3): Catalog IDs used across tests (must exist in data/)., _sample_chat_response(), test_chat_success()

### Community 8 - "Community 8"
Cohesion: 0.23
Nodes (11): clear_product_caches(), _embed_products(), _get_model(), _lexical_resolve(), message_looks_like_sku(), _normalize(), _product_document(), True when the text contains a catalog-style numeric code (5+ digits). (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (11): Chart, Tooltip, _histogram(), _lollipop(), SupplyMate · Operación — Streamlit assistant (FastAPI /chat + OC export)., Ranking: one categoric + one numeric → lollipop (data-to-viz)., Numeric distribution → histogram (ordered bins on X, counts on Y)., render_calculation() (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.48
Nodes (6): _as_num(), _as_str(), main(), Path, Split docs/perfumeria_enriched.xlsx into resource-oriented CSVs under data/.…, _write()

## Knowledge Gaps
- **1 isolated node(s):** `supplymate`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 60 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ProductNotFoundError` connect `Community 6` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `ProductMaster` connect `Community 5` to `Community 1`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `classify_intent()` connect `Community 0` to `Community 4`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `ProductNotFoundError` (e.g. with `chat()` and `get_product()`) actually correct?**
  _`ProductNotFoundError` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ProductMaster` (e.g. with `get_product()` and `get_master()`) actually correct?**
  _`ProductMaster` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `CatalogStore` (e.g. with `Inventory` and `ProductMaster`) actually correct?**
  _`CatalogStore` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `supplymate` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._