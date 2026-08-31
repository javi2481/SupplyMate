# Proposal: engineering-quality

## Why

The textbook *Ingeniería del Software II: Implementación, Pruebas y Mantenimiento* (Celi-Párraga et al., 2023) mapped against SupplyMate identified solid TDD/SDD and deterministic logic, but gaps in CI, requirement traceability, OWASP-minimal security, deployment smoke, performance smoke, and maintenance governance.

## What Changes

- New SDD change with specs for CI, security, traceability, deployment
- GitHub Actions: pytest + coverage on critical modules + Docker smoke
- `traceability-matrix.md` linking MUSTs from active changes to pytest tests
- OWASP-minimal hardening: input limits, prod error handler, rate limit on `/chat`, security headers
- `scripts/smoke_api.sh` / `.ps1` and `tests/test_performance.py`
- Maintenance docs: policy, bug template, change-request template, beta protocol, compatibility matrix, OSSTMM-lite checklist

## Non-Goals

- JWT auth, HTTPS termination, WAF
- Automated Streamlit E2E
- Full OSSTMM sections D–F
- BrowserStack / automated browser matrix

## Reference

- Informe: `docs/ingenieria-del-software-ii-implementacion-pruebas-y-mantenimiento.pdf`
