## Exploration: streamlit-native-shell

Fix Streamlit UI *composition* so SupplyMate matches the conversational navy/blue mockup. Not another generic CSS polish: Streamlit never nests later widgets inside split `st.markdown` open/close tags, so the previous visual-shell HTML wrappers render as empty bordered boxes.

### Current State

`ui-mockup-polish` (HEAD `7b18c29`) added class-based chrome (`sm-chart-card`, `sm-panel`, `sm-composer`, rail-row wrappers) that Streamlit cannot parent. Widgets (`st.altair_chart`, `st.caption`, `st.button`, `st.chat_input`) render as siblings. AppTests lock that anti-pattern by asserting the class strings in `at.markdown`. `ui-mockup-polish/verify-report.md` admitted visual review was AppTest + HTTP 200, not a real browser pass.

**Split-HTML wrappers (empty boxes):**

- `ui/components.py::render_chart_card` — `st.markdown("<div class='sm-chart-card'>")` → title/caption/`body()` → `</div>`
- `ui/streamlit_app.py::render_live_panel` — same for `sm-panel`
- `ui/threads/rail.py::_render_thread_rows` — same for `rail-row` / `rail-row-active`

**Color / layout drift vs mockup:**

- Charts: `ui/charts.py` lollipop uses `scheme="orangered"`; histogram maps bars through `COVERAGE_COLORS`. `COVERAGE_COLORS` / `HEALTH_COLORS` must stay for semantic strips (`render_coverage_strip` in static history), not for Explore charts.
- Explore KPIs (`ui/composition/kpi_policy.py::explore_kpi_cards`): Productos `#90CAF9`, Falta `HEALTH` orange, Quiebre `HEALTH` red, Cobertura `#AED581` green. Target: Falta/Quiebre stay; Cobertura (and Productos) use brand blue `SHELL_TOKENS["primary_accent"]` (`#1E88E5`). Do **not** invert `HEALTH_COLORS`.
- `st.set_page_config(layout="wide")` + sidebar CSS locked at 280px; no `.block-container` max-width.
- Hero in main (`ui/chrome.py::render_header`, `.sm-hero-title` 2.2rem) dominates the workspace. Sidebar footer already shows `APP_NAME`.
- New-chat CTA: visible copy `"+ Nuevo chat"`; `type="primary"` plus `[data-testid="stSidebar"] button[kind="primary"] { background: var(--sm-danger-accent) }` paints it danger red.
- `st.chat_message` has no `avatar=`; CSS uses `:has([data-testid=chatAvatarIcon-…])`.
- Fake composer chrome (`sm-composer` / clip `+`) sits above `st.chat_input` inside `st.bottom`.
- `pyproject.toml` floor is `streamlit>=1.38.0` while `st.bottom` is public since 1.57.0. `st.container(border=True)` is the native nesting primitive (widgets actually land inside the bordered block).

**Already-correct product shape (do not reopen):**

- `ui/layout_explore.py` is slim: compact scope + 4 KPIs + 2 charts. No next-step, table, or analyst. Unused kwargs are still passed from `render_live_panel` and from `tests/unit/ui/test_layout_apptest.py`. Do not re-add those surfaces. `ui-v2` `surfaces` still describes the older Explore order; this change must not restore it.
- Internal thread default title stays `"Nuevo chat"` (`ui/threads/store.py`, `tests/unit/ui/test_chat_threads.py`).

**Tests that encode the bug:**

- `tests/unit/ui/test_visual_shell_apptest.py::test_visual_shell_chart_card_wrapper_markup` asserts `sm-chart-card` in markdown
- `::test_streamlit_app_renders_composer_shell` asserts `sm-composer` in markdown
- `::test_visual_shell_header_uses_hero_markup` asserts `sm-hero-title` + product identity in main
- KPI/chart color tests do **not** yet lock accents (`test_composition_kpi_table.py` checks labels/icons only; `test_charts_selection.py` checks hit-layer selection only)

`openspec/config.yaml`: `strict_tdd: true`. Tests that encode the anti-pattern **must** be rewritten as RED tests of the new contract first. pytest green is not done; real visual review is a verify gate.

### Affected Areas

- `ui/components.py` — replace split `sm-chart-card` HTML with `st.container(border=True)`; keep KPI HTML cards (single `st.markdown` blob, actually nested)
- `ui/layout_explore.py` — still calls `render_chart_card`; no Explore surface expansion
- `ui/streamlit_app.py` — drop `sm-panel` split wrapper and `sm-composer` chrome; keep `st.bottom` + `st.chat_input`; add `avatar=` on `st.chat_message`; optional dead-kwarg cleanup at `render_live_panel` call site
- `ui/threads/rail.py` — native containers for thread rows; visible CTA `+ Nuevo recorte`; stop using danger-red primary
- `ui/charts.py` — single brand-blue scale for lollipop and histogram; keep importing `COVERAGE_COLORS` unused or drop import only (do not mutate the dict)
- `ui/composition/kpi_policy.py` — Cobertura accent → brand blue; Productos may share the same token; Falta/Quiebre stay `HEALTH_COLORS`
- `ui/theme.py` — **targeted delete only**: leftover wrapper/composer/avatar-hack CSS; add `.block-container` max-width; stop painting sidebar primary as `--sm-danger-accent`; shrink/remove `.sm-hero-*` dominance. Do not rewrite tokens wholesale. Keep `HEALTH_COLORS` / `COVERAGE_COLORS`
- `ui/chrome.py` — compact main header (mode, not giant product title); identity stays in sidebar
- `ui/composition/copy.py` — `NEW_CHAT = "+ Nuevo recorte"` (rail tests use the constant; thread-title tests stay on `"Nuevo chat"`)
- `pyproject.toml` — `streamlit>=1.57.0`
- `tests/unit/ui/test_visual_shell_apptest.py` — rewrite anti-pattern assertions (RED first)
- `tests/unit/ui/test_composition_kpi_table.py` — add accent-color contract
- `tests/unit/ui/test_charts_selection.py` — add single-blue scale contract (selection tests stay)
- `tests/unit/ui/test_thread_rail_apptest.py` — follows `ui_copy.NEW_CHAT`; may need “not danger” / no split `rail-row` HTML
- `tests/unit/ui/test_layout_apptest.py` — keep slim-Explore assertions; only touch if unused kwargs are cleaned
- `openspec/changes/ui-mockup-polish/specs/visual-shell/spec.md` — **MODIFY** chart-card (native container, not HTML wrap), composer (no fake shell), hero (identity in sidebar, compact main)
- `openspec/changes/ui-v2/specs/surfaces/spec.md` Chrome — **MODIFY** header identity location; do not restore next-step/table/analyst on live Explore

**Out of scope:** FastAPI, `app/core`, replenishment, metrics contracts, agents, APIs. No React/Next/Tailwind/custom Streamlit components.

### Approaches

1. **Native Streamlit containers + targeted token/CSS surgery** — `st.container(border=True)` for chart cards and rail rows; drop split HTML; constrain `.block-container`; brand-blue charts/coverage KPI; keep `st.bottom`; explicit `avatar=`; delete leftover CSS only.
   - Pros: Widgets actually nest; matches Streamlit’s layout model; CSS leftover shrinks; AppTests can assert *absence* of wrapper classes plus presence of titles/`chat_input`; verify gate can look at real cards
   - Cons: AppTest cannot prove pixels/nesting (verify must be a real browser pass); `visual-shell` and `surfaces` Chrome need MODIFIED deltas
   - Effort: Medium

2. **More CSS to fake parent HTML** — keep split markdown wrappers; try `st.html`, negative margins, or `:has()` to visually glue sibling widgets into empty boxes.
   - Pros: Low code churn; existing AppTests stay green
   - Cons: Streamlit still does not nest; empty boxes remain; more fragile `data-testid` CSS; repeats the failed `ui-mockup-polish` strategy
   - Effort: Low (and wrong)

3. **Leave wrappers and only recolor** — swap `orangered` / KPI greens for brand blue; leave `sm-*` HTML in place.
   - Pros: Smallest diff
   - Cons: Empty bordered boxes stay; composer clip still fake; hero still dominates; CTA still danger-red; does not match mockup composition
   - Effort: Low (and incomplete)

### Recommendation

**Approach 1.** Native containers are the only way Streamlit will put charts inside cards. Recolor-without-reparenting (3) and CSS-glue (2) cannot fix the audited root cause.

Implementation sketch (for propose/design, not apply):

| Surface | Do | Do not |
|---------|----|--------|
| Chart cards | `with st.container(border=True):` title + caption + `body()` | Split `sm-chart-card` markdown |
| Live panel | Existing `st.container()` around `render_live_panel` is enough | `sm-panel` open/close markdown |
| Rail rows | `st.container(border=is_active)` (or no wrapper + button type) | `rail-row` open/close markdown |
| Width | CSS `.block-container { max-width: … }` | Extra HTML workspace wrapper |
| Charts | One brand-blue Altair scale | Mutate `COVERAGE_COLORS` / `HEALTH_COLORS` |
| Coverage KPI | `SHELL_TOKENS["primary_accent"]` | Recolor Falta/Quiebre |
| Composer | `with st.bottom: st.chat_input(...)` only | `sm-composer` decorative HTML |
| Avatars | `st.chat_message(role, avatar=…)` (analytics vs person) | `:has([data-testid=…])` as the primary mechanism |
| New chat | Visible `+ Nuevo recorte`; sidebar CTA uses primary/brand, not `--sm-danger-accent` | Change `DEFAULT_TITLE` / thread semantics |
| Hero | Compact mode in main; identity in sidebar | 2.2rem product title competing with the chat |
| Theme | Delete leftover wrapper/composer/avatar-hack rules | Wholesale `theme.py` rewrite |
| Explore kwargs | Optional cleanup if tests stay green | Re-adding next-step/table/analyst |

**TDD (mandatory):** rewrite `test_visual_shell_chart_card_wrapper_markup` and `test_streamlit_app_renders_composer_shell` (and hero markup) as RED tests of the new contract *before* implementation: no split wrapper class in markdown; title/`chat_input` still present; coverage KPI accent is brand blue; Altair scale is not `orangered` and histogram range is not `COVERAGE_COLORS`. Then implement. Verify is a real visual pass, not HTTP 200.

### Risks

- AppTest cannot certify visual nesting; shipping on pytest-only would repeat `ui-mockup-polish`’s false “done”
- `visual-shell` currently *requires* hero-in-main and allows composer decorative HTML — deltas must MODIFY those requirements or apply will “fail” the old spec
- `surfaces` live-Explore order (next-step + table + AI reading) is already unimplemented in `layout_explore.py`; a careless delta could try to restore it
- Histogram currently *is* the semantic coverage coloring; switching to brand blue is intentional for Explore charts only — static `render_coverage_strip` must keep `COVERAGE_COLORS`
- Streamlit floor bump (`>=1.57.0`) can break local/CI if the env still has 1.38–1.56
- Sidebar 280px lock + `.block-container` max-width may feel tight on small laptops; verify both desktop widths
- Active-rail CSS today uses an orange left bar on a wrapper that does not wrap; native `border=True` will look different — align active accent to brand blue, not leftover orange/danger
- Optional unused-kwarg cleanup touches `render_live_panel` + layout AppTest harnesses; keep it off the visual critical path if it threatens TDD focus

### Ready for Proposal

Yes. Orchestrator should tell the user: the gap is Streamlit composition (native containers), not more CSS. Recommend approach A; keep Explore slim; TDD rewrites the tests that currently lock the HTML anti-pattern; verify in a real browser.

Settled decisions to carry into `proposal.md` (do not re-litigate): native `st.container(border=True)`; Falta=orange / Quiebre=red / coverage KPI + charts = brand blue; `.block-container` width; keep `st.bottom`, drop fake composer; explicit `avatar=`; visible `+ Nuevo recorte`; Streamlit `>=1.57.0`; no FastAPI/core/React; no `HEALTH_COLORS` / `COVERAGE_COLORS` global invert; no Explore next-step/table/analyst revival.
