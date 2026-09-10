# Design: semantic-correctness

## Policy

Order-up-to / periodic review:

```
T = demand(7) + demand(L) + safety_stock
qty = max(0, ceil(T - on_hand))
```

`reorder_point` is not an input to qty. It only drives `health_bucket == stockout_risk`.

## LLM vs Python

| Surface | Owner | Guard |
|---------|--------|--------|
| Intent (hard paraphrases) | Groq | golden CSV + `@pytest.mark.llm` |
| Slice / qty / filters | Python | existing unit tests |
| Insight / commit JSON | Groq | `insight_validator` + CI fixtures |
| SKU explanation | Groq | orphan integers → deterministic text |

## Logs

One JSON line per `Runner.run`: `{event, agent, latency_ms, intent, fallback_used, insight_source}`. No prompt bodies. SDK tracing stays disabled on Groq.
