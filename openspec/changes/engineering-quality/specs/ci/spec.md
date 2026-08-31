# CI spec

## Requirements

- CI MUST run `pytest` on every push and pull request without live LLM calls
- CI MUST fail if any existing test fails
- CI MUST report coverage for critical modules: `app/replenishment.py`, `app/services/scope.py`, `app/services/catalog_service.py`, `app/services/dashboard.py`
- Coverage on those modules MUST be at least 85%
- CI MUST build Docker image and run `scripts/smoke_api.sh` against the container
- Performance tests (`@pytest.mark.performance`) MUST run only on `main` branch workflow
