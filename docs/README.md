# Documentation index

Public docs are grouped by audience. Contract docs are bilingual (EN canonical + ES twin).

## Contract — how the system works

| Doc | Purpose |
|-----|---------|
| [`contract/architecture.md`](contract/architecture.md) | LLM vs Python boundary, surfaces, **repo layers** |
| [`contract/evaluation.md`](contract/evaluation.md) | CI, pytest layout, golden fixtures, coverage gates |
| [`contract/data-contract.md`](contract/data-contract.md) | CSV catalog schema and regeneration |

Spanish twins: `*.es.md` in the same folder.

## Operations — run, maintain, audit

| Doc | Purpose |
|-----|---------|
| [`operations/maintenance-policy.md`](operations/maintenance-policy.md) | Preventive maintenance cadence |
| [`operations/performance-profile.md`](operations/performance-profile.md) | Latency smoke thresholds |
| [`operations/security-audit-osstmm-lite.md`](operations/security-audit-osstmm-lite.md) | Lite security checklist |
| [`operations/security-deps.md`](operations/security-deps.md) | Dependency audit notes |
| [`operations/compatibility-matrix.md`](operations/compatibility-matrix.md) | Browser / OS matrix |
| [`operations/beta-test-protocol.md`](operations/beta-test-protocol.md) | Beta UX scenario |

## Templates

| Doc | Purpose |
|-----|---------|
| [`templates/change-request-template.md`](templates/change-request-template.md) | Large change intake |

## Related (not under `docs/`)

| Path | Purpose |
|------|---------|
| [`../app/README.md`](../app/README.md) | Application code layers |
| [`../tests/README.md`](../tests/README.md) | Test suite layers |
| [`../openspec/`](../openspec/) | Internal SDD specs per change |
| [`../notes/research/`](../notes/research/) | Research JSON (non-runtime) |
| [`../notes/assets/`](../notes/assets/) | PDF/XLSX reference files (not public contract) |
