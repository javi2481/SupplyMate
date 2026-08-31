# Traceability spec

## Requirements

- Every MUST statement in active change specs (`mvp-core`, `dual-surface-analytics`, `interactive-drilldown`) MUST appear in `traceability-matrix.md` with at least one test or manual verification id
- Automated MUSTs MUST link to `tests/test_*.py::test_*`
- UI-only MUSTs MUST link to manual checklist ids (UX-01 … UX-06)
- Gaps MUST be closed with minimal new tests before change verify PASS
