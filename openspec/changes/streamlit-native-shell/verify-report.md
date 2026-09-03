# Verify report: streamlit-native-shell

## pytest

- Focused RED/GREEN commands (por work unit):
  - PR1: `pytest tests/unit/ui/test_visual_shell_apptest.py tests/unit/ui/test_thread_rail_apptest.py tests/unit/ui/test_layout_apptest.py -k "wrapper_markup or composer_shell or rail" -m "not llm"`
  - PR2: `pytest tests/unit/ui/test_composition_kpi_table.py tests/unit/ui/test_charts_selection.py -m "not llm"`
  - PR3: `pytest tests/unit/ui/test_visual_shell_apptest.py -k "hero_markup or copy_constants or theme_sidebar or streamlit_floor" -m "not llm"`
- Final suite: `pytest tests/unit/ui/ -m "not llm"`
- Result: `62 passed in 17.63s`

## TDD evidence

| Work unit | RED evidence | GREEN module(s) | Focused result |
|-----------|--------------|-----------------|----------------|
| Native composition | AppTests prohibiendo `sm-chart-card` / `sm-composer` / `sm-panel` / `rail-row` partidos | `ui/components.py`, `ui/streamlit_app.py`, `ui/threads/rail.py` | wrappers + rail verdes |
| Palette | KPI Productos+Cobertura azul; charts sin `orangered` / sin `COVERAGE_COLORS` | `ui/composition/kpi_policy.py`, `ui/charts.py` | KPI + charts verdes |
| Chrome / copy / deps | Hero sin `sm-hero-title`; `+ Nuevo recorte`; CTA primary no danger; `streamlit>=1.57.0` | `ui/chrome.py`, `ui/composition/copy.py`, `ui/theme.py`, `ui/streamlit_app.py`, `pyproject.toml` | copy/hero/theme verdes |

## Spec coverage

| Spec | Covered by |
|------|------------|
| `visual-shell` | `tests/unit/ui/test_visual_shell_apptest.py`, `ui/theme.py` CSS + tokens |
| `surfaces` | `tests/unit/ui/test_layout_apptest.py` (Explore slim) |
| `ui-composition` | `tests/unit/ui/test_composition_kpi_table.py`, chart AppTests |
| `chat-threads` | `tests/unit/ui/test_thread_rail_apptest.py`, `NEW_CHAT` copy |

## Runtime harness (REAL browser)

- API: `uvicorn app.api:app --host 127.0.0.1 --port 8000` → startup OK
- UI: `streamlit run ui/streamlit_app.py --server.port 8502 --server.headless true` → `http://localhost:8502`
- Browser: gstack `browse` (goto + snapshot + DOM asserts + screenshot)

### Checklist visual

| Check | Result |
|-------|--------|
| Sin wrappers HTML partidos (`sm-panel` / `sm-chart-card` / `sm-composer` / `sm-hero-title`) | OK — `emptyWrappers: 0` |
| Cards nativas `st.container(border=True)` con título + chart | OK — ambos charts visibles |
| Charts Explore en azul de marca `#1E88E5` | OK — lollipop + histograma |
| KPI Productos/Cobertura azul; Falta naranja `#FB8C00`; Quiebre rojo `#E53935` | OK |
| Hero compacto (`Reposición inteligente · Explorando`) | OK |
| CTA `+ Nuevo recorte` azul (no danger) | OK |
| Composer `st.chat_input` en `st.bottom` | OK |
| Avatares Material en `st.chat_message` | OK (person / analytics) |

### Nota de fix en verify

- El histograma de cobertura quedaba con embed Vega vacío (`height: 0`) cuando `selection_point(nearest=True)` corría en columnas Streamlit.
- GREEN mínimo: `histogram(..., nearest=False)` en `ui/charts.py`. Tras el cambio, embed `h=280` con 5 barras `#1E88E5`.

Evidencia: `.gstack-verify-final.png` (sesión local; no es artefacto de release).

## Graphify

- `graphify update .` → succeeded
- Rebuilt graph: `1839 nodes`, `3597 edges`, `154 communities`

## Fuera de alcance (confirmado no tocado)

- FastAPI / replenishment / metrics contracts / agents
- Rewrite de tokens semánticos `HEALTH_COLORS` / `COVERAGE_COLORS`
- Restaurar dashboard largo en Explore
- Cambio de `DEFAULT_TITLE` interno (`"Nuevo chat"`)

## Status

- apply: done
- verify: done (pytest + browser real)

## Post-verify audit follow-up

- Security review ([Review](153ffa56-2809-4736-bb4e-e64de28f12a9)): no medium+/critical findings; XSS surface reduced.
- Bugbot ([Review](1652f4ba-8905-43d6-b900-c024e48bb100)): fixed misleading static coverage caption (rojo/verde vs brand-blue bars).
- Hardening: `html.escape` on KPI HTML fields; `streamlit>=1.57.0,<2`; merge of live dashboards requires both `by_category` and `coverage`.
- R1 risk ([Review](b35c9ed9-3e4c-46ca-919b-83b5625a26d7)): no merge-blocking risks.
