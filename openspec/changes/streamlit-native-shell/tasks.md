# Tasks: Streamlit Native Shell

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 550–850 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 composition → PR2 palette → PR3 chrome → PR4 verify |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

App: `streamlit run ui/streamlit_app.py --server.port 8502` + browser. Chain bases: PR1=tracker; PR2=PR1; PR3=PR2.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Native composition | PR 1 | `pytest tests/unit/ui/test_visual_shell_apptest.py tests/unit/ui/test_thread_rail_apptest.py tests/unit/ui/test_layout_apptest.py -k "wrapper_markup or composer_shell or rail" -m "not llm"` | App; nested cards; no empty boxes; bottom composer | `ui/components.py`, `ui/streamlit_app.py` wrappers, `ui/threads/rail.py` |
| 2 | Palette | PR 2 | `pytest tests/unit/ui/test_composition_kpi_table.py tests/unit/ui/test_charts_selection.py -m "not llm"` | App; blue charts; Falta orange; Quiebre red | `ui/composition/kpi_policy.py`, `ui/charts.py` |
| 3 | Chrome/copy/deps | PR 3 | `pytest tests/unit/ui/test_visual_shell_apptest.py tests/unit/ui/test_thread_rail_apptest.py tests/unit/ui/test_chat_threads.py -k "hero_markup or recorte" -m "not llm"` | App; compact header; CTA not danger; avatars | `ui/chrome.py`, `ui/composition/copy.py`, `ui/theme.py`, `pyproject.toml`, `ui/streamlit_app.py` |
| 4 | Verify | last | `pytest tests/unit/ui/ -m "not llm"` | REAL browser on a free port (4.2). pytest-only ≠ done | `verify-report.md`; no app rollback |

## Phase 1: Native composition

- [x] 1.1 RED rewrite `test_visual_shell_chart_card_wrapper_markup` and `test_streamlit_app_renders_composer_shell` in `tests/unit/ui/test_visual_shell_apptest.py`: no `sm-chart-card`/`sm-composer`/`sm-panel`; titles+`chat_input` remain. FAIL on main. Do not rewrite hero here (that is 3.0).
- [x] 1.2 GREEN `ui/components.py::render_chart_card` → `st.container(border=True)`. Keep KPI single-blob HTML.
- [x] 1.3 GREEN `ui/streamlit_app.py`: drop `sm-panel`/`sm-composer`; keep `st.bottom` + `st.chat_input`.
- [x] 1.4 RED `tests/unit/ui/test_thread_rail_apptest.py`: no split `rail-row` HTML.
- [x] 1.5 GREEN `ui/threads/rail.py`: `st.container(border=is_active)` per row.
- [x] 1.6 Keep slim Explore in `tests/unit/ui/test_layout_apptest.py`. No next-step/table/analyst.

## Phase 2: Palette

- [x] 2.1 RED `tests/unit/ui/test_composition_kpi_table.py`: Productos+Cobertura=`SHELL_TOKENS["primary_accent"]`; Falta/Quiebre=`HEALTH_COLORS`.
- [x] 2.2 GREEN `ui/composition/kpi_policy.py`. Do not mutate `HEALTH_COLORS`/`COVERAGE_COLORS`.
- [x] 2.3 RED `tests/unit/ui/test_charts_selection.py`: not `orangered`; histogram not `COVERAGE_COLORS`; keep selection.
- [x] 2.4 GREEN `ui/charts.py` one brand-blue scale.

## Phase 3: Chrome / copy / deps

- [x] 3.0 RED rewrite `test_visual_shell_header_uses_hero_markup`: no giant `sm-hero-title` in main; compact mode label remains. FAIL until 3.1.
- [x] 3.1 GREEN `ui/chrome.py` compact mode header. Identity in sidebar.
- [x] 3.2 RED visible `+ Nuevo recorte`; CTA not `--sm-danger-accent` if testable.
- [x] 3.3 GREEN `ui/composition/copy.py` `NEW_CHAT="+ Nuevo recorte"`; `ui/theme.py` brand sidebar primary. Do not change `DEFAULT_TITLE`.
- [x] 3.4 RED avatar presence if testable; else skip to 3.5.
- [x] 3.5 GREEN `st.chat_message(..., avatar=)` in `ui/streamlit_app.py`; delete avatar-hack CSS in `ui/theme.py`.
- [x] 3.6 RED `pyproject.toml` floor `>=1.57.0` if testable.
- [x] 3.7 GREEN `streamlit>=1.57.0`; `.block-container` ~1100–1150px; delete leftover wrapper/composer/hero CSS only.

## Phase 4: Verify

- [x] 4.1 `pytest tests/unit/ui/ -m "not llm"`.
- [x] 4.2 Free-port Streamlit; REAL browser: no empty boxes, blue charts, KPI palette, compact workspace, bottom composer. pytest-only ≠ done.
- [x] 4.3 `graphify update .`; write `openspec/changes/streamlit-native-shell/verify-report.md`.

- [ ] 5.1 Optional: unused Explore kwargs cleanup — off critical path.
