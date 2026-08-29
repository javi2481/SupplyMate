# Proposal: mvp-core

## Why

SME distributors need a simple answer to: “How much should I order of product X for the next 7 days?” Manual spreadsheets are error-prone. SupplyMate provides a chat-style MVP where an LLM orchestrates data tools and deterministic Python computes the reorder quantity.

## What Changes

- FastAPI service with `POST /chat` and `GET /health`
- OpenAI Agents SDK agent with three function tools over CSV data
- Deterministic replenishment calculation in Python
- Structured response: answer, product_id, recommended_quantity
- pytest suite without live LLM calls
- Docker packaging and README

## Capabilities

- Replenishment calculation (horizon 7d, history 30d, lead time, safety stock)
- CSV-backed tools: inventory, sales history, replenishment params
- Agent two-phase flow: gather tools → calculate → explain
- HTTP API for chat recommendations

## Non-Goals

- RAG, embeddings, vector DBs
- LangChain / LangGraph / multi-agent
- Frontend, database, Kubernetes
- Forecasting, EOQ, seasonality, ML

## Rollback

Delete the service / revert the change directory; no production data stores in MVP.

## Risks

- LLM may skip tools → mitigated by SupplyContext readiness checks and Python-owned quantity
- CSV path issues in Docker → fixed DATA_DIR relative to package
