# Tasks: engineering-quality

## Phase 0 — SDD

- [x] 0.1 proposal, design, specs, tasks, traceability-matrix

## Phase 1 — Traceability audit

- [x] 1.1 Complete traceability-matrix.md
- [x] 1.2 Add minimal tests for gaps

## Phase 2 — Security (Strict TDD)

- [x] 2.1 RED/GREEN input limits + scope sanitization
- [x] 2.2 RED/GREEN prod error handler + security headers
- [x] 2.3 RED/GREEN chat rate limit + tests/security/test_security.py

## Phase 3 — CI

- [x] 3.1 pyproject.toml pytest-cov + coverage config
- [x] 3.2 .github/workflows/ci.yml

## Phase 4 — Smoke + performance

- [x] 4.1 scripts/smoke_api.sh + smoke_api.ps1
- [x] 4.2 tests/performance/test_performance.py + docs/operations/performance-profile.md

## Phase 5 — Maintenance + audit docs

- [x] 5.1 maintenance-policy, bug template, change-request-template
- [x] 5.2 beta-test-protocol, compatibility-matrix, security-audit-osstmm-lite, security-deps

## Phase 6 — UX + close

- [x] 6.1 UX checklist documented (manual procedure)
- [x] 6.2 verify-report, README, openspec/config.yaml coverage:true
