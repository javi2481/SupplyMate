# Proposal: natural-query-interpretation

## Why

The chat router still asks «¿puedo mapear esto a un SKU?» and returns 404 when it cannot. The product already has drill-down (`AnalyticalScope`, `ReplenishmentSlice`, live panel, OC export). Users express themselves in natural language («¿cuántos jabones y shampoo debo comprar?») and expect an **analytical surface** seeded by that question—not a SKU lookup error.

This is a **core quality improvement** inside current scope, not a new platform.

## What Changes

- Add `QueryInterpretation` layer: business intent + entity references (LLM + rules)
- Add `resolve_references()`: catalog-driven GROUP / EXACT / AMBIGUOUS (Python only)
- Extend `AnalyticalScope` for heterogeneous groups (subcategories + optional `ResolvedGroup`)
- Extend `ChatResponse` with `scope`, `interpretation`, `group_summaries`
- Chat opens dashboard with **initial scope** from interpretation (Streamlit stops resetting to root)
- Deterministic multi-group summary text (Jabones 48 · Shampoo 31 · Total 79)
- Golden cases for interpretation + resolution (no LLM in CI for resolution path)

## Non-Goals

- NL→SQL, ad-hoc query language, or user-visible filter dimensions
- Re-introducing embeddings / semantic product search
- Full SpaCy/NLTK pipeline as primary stack
- Conversational memory across sessions (phase 1)
- Always-on confirmation UI for every message

## Success Criteria

| Input | Expected |
|-------|------------|
| `¿Qué productos tengo que comprar?` | Root dashboard, `references=[]` |
| `¿Cuántos jabones debo comprar?` | Filtered dashboard + summary for Jabones group |
| `¿Cuántos jabones y shampoo debo comprar?` | Comparative summary + multi-group scope + dashboard |
| `¿Cuánto pedir de 6033436?` | Single SKU (unchanged) |
| `¿Qué jabones tienen riesgo?` | `inventory_risk` + group scope + health filter |
| `¿Cuánto cuidado debo comprar?` | Disambiguation prompt (low confidence) |
