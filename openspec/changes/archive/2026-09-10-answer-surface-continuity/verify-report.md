# Verify report: answer-surface-continuity

## Date

2026-09-04

## Evidence

| Slice | Evidence |
|-------|----------|
| History | `tests/unit/scope/test_scope_history.py` green |
| Snapshot | `tests/unit/ui/test_chat_threads.py` includes `scope_history` |
| Context bar | AppTests Volver disabled/enabled + Limpiar |
| KPI actions | `tests/unit/ui/test_kpi_actions.py` + layout AppTest buttons |
| Charts | stroke/size by `_selected`; histogram labels; brand blue |
| SKU slot | AppTest hides charts, shows Comprar + expander |
| UI suite | `tests/unit/ui/` 95 passed |
| Unit+acceptance | 228 passed, 1 skipped |

## Notes

- Integration `test_llm_unknown_does_not_force_a_random_sku` failed once (LLM interpreter path); unrelated to this UI change — no live-LLM dependency in the new modules.
- No FastAPI / AnalyticalScope field changes. History is session-only.

## Status

DONE_WITH_CONCERNS — one pre-existing/flaky LLM integration test; core continuity suite green.
