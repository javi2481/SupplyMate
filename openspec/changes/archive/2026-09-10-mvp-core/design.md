# Design: mvp-core

## Architecture

```
User → POST /chat → run_supplymate
  → Phase 1: Agent + function tools → SupplyContext
  → calculate_replenishment (Python)
  → Phase 2: explain Agent (no tools)
  → ChatResponse
```

Principle: **LLM orchestrates, deterministic code decides.**

## Stack decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent runtime | openai-agents | Official thin loop; @function_tool + Runner |
| Data | CSV + stdlib csv | Small dataset; no DB |
| Calc | replenishment.py | Testable without LLM |
| API | FastAPI | Async + Pydantic |
| Model default | gpt-4o-mini | Cheap demo model |

## Components

- `app/core/models.py` — ChatRequest/Response, DTOs, SupplyContext
- `app/agent/tools.py` — CSV loaders + @function_tool wrappers
- `app/core/replenishment.py` — formula with HORIZON_DAYS=7, HISTORY_DAYS=30
- `app/agent/runner.py` — two-phase Runner flow
- `app/api.py` — /chat, /health
- `app/config.py` — DATA_DIR, OPENAI_API_KEY, model

## Formula

```
avg_daily = total_units_sold_last_30 / 30
demand_horizon = avg_daily * 7
demand_lead = avg_daily * lead_time_days
stock_target = demand_horizon + demand_lead + safety_stock
recommended = max(0, stock_target - current_stock)
```

## Testing strategy

- Unit tests for replenishment and CSV tools (no API key)
- Agent tests mock Runner.run
- API tests use TestClient and mock run_supplymate

## Threats (MVP)

| Threat | Mitigation |
|--------|------------|
| LLM invents quantity | Quantity taken only from ReplenishmentResult |
| Missing tool data | Fail if SupplyContext not ready |
| Unknown SKU | Domain error → HTTP 404 |
