# Tasks: mvp-core

## Phase 0 — Scaffold

- [x] 0.1 Create `pyproject.toml` with fastapi, uvicorn, pydantic, openai-agents, pytest
- [x] 0.2 Create package layout `app/` and empty modules placeholders as needed for imports
- [x] 0.3 Create CSV datasets under `data/` (PROD-001 demo + high-stock SKU)

## Phase 1 — Replenishment (Strict TDD)

- [x] 1.1 RED/GREEN/TRIANGULATE average daily demand
- [x] 1.2 RED/GREEN/TRIANGULATE stock target and recommended quantity (incl. zero when stock > target)

## Phase 2 — Tools (Strict TDD)

- [x] 2.1 RED/GREEN/TRIANGULATE get_inventory valid + unknown product
- [x] 2.2 RED/GREEN/TRIANGULATE get_sales_history valid + unknown product
- [x] 2.3 RED/GREEN/TRIANGULATE get_replenishment_params valid + unknown product

## Phase 3 — Agent (Strict TDD)

- [x] 3.1 RED/GREEN/TRIANGULATE run_supplymate returns Python quantity with mocked Runner
- [x] 3.2 RED/GREEN unknown product surfaces as domain error

## Phase 4 — API (Strict TDD)

- [x] 4.1 RED/GREEN GET /health
- [x] 4.2 RED/GREEN/TRIANGULATE POST /chat success + 404

## Phase 5 — Ship

- [x] 5.1 Dockerfile + `.env.example` (triangulation skipped: structural)
- [x] 5.2 README with architecture ASCII, formula, curl, tests, Docker
- [x] 5.3 Verify report and mark tasks complete
