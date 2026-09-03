# Verify report: ui-v2

## pytest

- Command: `pytest -m "not llm"`
- Result: 263 passed, 2 skipped, 1 deselected
- New: `tests/unit/ui/test_composition_*.py`, `tests/unit/ui/test_layout_apptest.py`
- Regression: suggested filters, panel modes, guidance plan included in the suite

## TDD evidence

| Spec | RED test | GREEN module |
|------|----------|--------------|
| compose_next_step | `test_composition_next_step.py` | `ui/composition/next_step.py` |
| KPI policy | `test_composition_kpi_table.py` | `ui/composition/kpi_policy.py` |
| Table / Señal | same | `ui/composition/table_policy.py` |
| Unfreeze | `test_composition_chat_scope.py` | `ui/composition/chat_policy.py` |
| Explore/Commit layout | `test_layout_apptest.py` | `ui/layout_explore.py`, `ui/layout_commit.py` |

## Graphify

`graphify update .` — AST rebuilt (1464 nodes).

## Manual leftover

Live design-review on `:8501` (empty home, ask, next step, commit unfreeze confirm, mobile sidebar) was not re-run in this apply session. Refresh the running Streamlit process to pick up `ui/` changes.
