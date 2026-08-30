# Proposal: dual-surface-analytics

> **Superseded (runtime):** no separate Analytics door. Chat dashboard only; no Superset/DuckDB.

## Why

SupplyMate already answers “how much should I order?” via an agent and deterministic Python.
Users also need to understand inventory health (“what is going on?”). Putting both in Streamlit
turns the assistant into a pseudo-BI tool and weakens the interview narrative.

## What Changes

- Shared metrics layer (`days_of_supply`, health buckets, canonical labels)
- DuckDB analytics warehouse materializing `analytics_sku` from Python (same formula)
- Enriched purchase list + CSV purchase-order export (operation surface)
- Streamlit branded as **SupplyMate · Operación** with deep-link to Analytics
- Optional Apache Superset via Compose with **one** Inventory & Replenishment dashboard
- Docs/README describing one product, two doors

## Capabilities

- Metrics: coverage and inventory health buckets with stable English labels
- Analytics DB: regenerable DuckDB from CSVs + Python materialization
- Purchase export: barcode + quantity CSV for purchase orders
- Surfaces: Operation vs Analytics UX separation and shared vocabulary

## Non-Goals

- Postgres, dbt, Airflow, Spark, Kafka
- Embedding Superset inside Streamlit
- Second Superset dashboard or demand-trend time series (no daily series)
- Changing replenishment formula or adding agent tools
- `/analytics/health` product UI (would compete with Superset)

## Rollback

Remove `openspec/changes/dual-surface-analytics/`, DuckDB script/deps, Compose/Superset docs,
and revert Streamlit/API enrichment.

## Risks

- Superset + DuckDB fragile on Windows → document minimal mode (API + Streamlit only)
- Looking like two unrelated apps → shared branding, labels, deep-link, UX checklist in verify
