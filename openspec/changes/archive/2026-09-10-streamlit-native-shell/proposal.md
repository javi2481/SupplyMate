# Proposal: Streamlit Native Shell

## Intent

Split HTML wrappers (`sm-chart-card`, `sm-panel`, `sm-composer`, rail-row) do not nest Streamlit widgets, so mockup chrome is empty boxes. Need native cards, real `st.chat_input`, sidebar identity, stable health colors.

**Assumed (settled; no question round):** native containers; Falta=orange / Quiebre=red; Coverage+Productos+charts=brand blue; no palette invert; no Explore restore.

## Scope

### In Scope

- Native `st.container(border=True)` for chart cards and rail rows; delete split HTML wrappers
- Keep `st.bottom` + `st.chat_input` only; explicit `avatar=`; compact hero (mode in main, identity in sidebar)
- `.block-container` max-width; brand-blue Explore charts; Coverage+Productos brand blue; CTA `+ Nuevo recorte` not danger red
- `streamlit>=1.57.0`; leftover wrapper/composer/avatar-hack CSS delete only
- TDD: RED-rewrite wrapper AppTests first; verify = real browser (pytest green ≠ done)

### Out of Scope

- FastAPI, `app/core`, replenishment, metrics, agents, APIs, React/custom components
- Wholesale `theme.py` rewrite; palette invert; restoring live Explore sequence; changing `DEFAULT_TITLE`

## Capabilities

### New Capabilities

- None

### Modified Capabilities

- `visual-shell`: native chart cards; no fake composer; compact hero
- `surfaces`: identity in sidebar + compact mode; MUST NOT restore ui-v2 Explore sequence
- `ui-composition`: Coverage/Productos accents → brand blue; `NEW_CHAT = "+ Nuevo recorte"`
- `chat-threads`: visible CTA `+ Nuevo recorte`; `DEFAULT_TITLE` stays `"Nuevo chat"`

## Approach

**Approach A.** Reject CSS-glue and recolor-only.

- `st.container(border=True)` for charts/rail; drop `sm-panel` wrap
- Width via `.block-container`; charts use `SHELL_TOKENS["primary_accent"]`; static strip MAY keep `COVERAGE_COLORS`
- `st.chat_message(..., avatar=)`; delete leftover CSS; sidebar primary not `--sm-danger-accent`
- RED first: no wrapper classes in markdown; `chat_input` present; KPI/chart color contracts

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `ui/components.py`, `chrome.py`, `theme.py` | Modified | Native cards; compact hero; targeted CSS |
| `ui/streamlit_app.py` | Modified | Drop wrappers; `avatar=`; keep `st.bottom` |
| `ui/threads/rail.py`, `composition/copy.py` | Modified | Native rows; `+ Nuevo recorte` |
| `ui/charts.py`, `composition/kpi_policy.py` | Modified | Brand-blue charts/KPIs |
| `pyproject.toml` + UI AppTests in explore | Modified | Floor 1.57; RED new-contract tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| AppTest cannot prove nesting | High | Verify = real browser |
| `surfaces` delta restores Explore | Med | Lock slim Explore |
| Floor `>=1.57.0` breaks older envs | Med | Pin in `pyproject.toml` |

## Rollback Plan

Revert the branch. No data migration. Thread JSON / `DEFAULT_TITLE` stay `"Nuevo chat"`.

## Dependencies

- Streamlit `>=1.57.0`; prior `ui-v2`, `chat-shell`, `ui-mockup-polish`

## Success Criteria

- [ ] No split wrappers; native bordered chart cards; composer is `st.bottom` + `st.chat_input`
- [ ] Falta orange, Quiebre red, Coverage+Productos+charts brand blue; visible `+ Nuevo recorte`; internal `"Nuevo chat"`
- [ ] RED-then-GREEN AppTests; real browser visual review passes
