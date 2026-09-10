# Design: llm-drilldown-insights

## Ask / Agent

| Mode | UI | LLM | Export |
|------|-----|-----|--------|
| explore | Explorar | `DashboardInsight` | disabled |
| commit | Armar OC | `CommitSummary` | `frozen_scope` CSV |

## Flow

`GET /slice` always first (fast). `POST /analyze` optional with debounce in UI.

Python: `replenishment_slice` + `insight_validator`. LLM: narrative only.
