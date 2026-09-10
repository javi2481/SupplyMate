# Verify: natural-query-interpretation

Date: 2026-08-31

## pytest

```
pytest -m "not llm and not performance" -q
185 passed, 1 skipped, 3 deselected
```

## Manual smoke (recommended)

| Query | Expected |
|-------|----------|
| ¿Cuántos jabones debo comprar? | mode=explore, scope category Jabon de Tocador, panel filtrado |
| ¿Cuántos jabones y shampoo debo comprar? | 2 group summaries, scope cat+subcat |
| ¿Qué jabones tienen riesgo? | health_buckets stockout_risk |
| ¿Cuánto cuidado debo comprar? | mode=disambiguation, options |
| ¿Cuánto pedir de 6033436? | mode=single, qty 173 |

## API checks

- `POST /chat` returns `scope`, `interpretation`, `group_summaries` on explore
- `GET /replenishment/slice?subcategory=Shampoo` filters correctly

## Non-goals confirmed

- No embeddings reintroduced
- No NL→SQL
- LLM optional for interpret (rules first); resolution 100% Python
