# Catalog integration — extends mvp-core with unified master + REST

## Goal

Integrate 5 resource CSVs as simulated API, expose ProductMaster + deterministic replenishment REST, enrich chat response while keeping 3 agent tools and unchanged formula.

## Tasks

- [x] ProductMaster model + store loads all CSVs including prices
- [x] docs/api-simulada.md
- [x] catalog_service.py
- [x] REST /products/search, /products/{id}, /products/{id}/replenishment
- [x] ChatResponse enriched; agent explain with full JSON
- [x] Streamlit + demo_queries.ps1 + README
- [x] Tests: store, catalog_service, API REST
