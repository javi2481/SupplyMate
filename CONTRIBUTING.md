# Contributing to SupplyMate

Thank you for your interest in SupplyMate. This project is **MIT** licensed.

## Getting started

```bash
git clone https://github.com/javi2481/SupplyMate.git
cd SupplyMate
python -m venv .venv
pip install -e ".[dev]"
cp .env.example .env
pytest -m "not performance and not llm"
```

On Windows, activate `.venv\Scripts\activate` before running tests.

## Before you open a PR

1. Run `pytest -m "not performance and not llm"` — it must pass.
2. Keep changes focused; match existing style in the files you touch.
3. For slice/scope, qty formula, or eval contract changes, read [`docs/contract/architecture.md`](docs/contract/architecture.md) first.
4. Do not commit secrets (`.env`, API keys).

## Issues and pull requests

- **Bugs:** open an issue with repro steps, expected vs actual, and pytest output if relevant.
- **Features:** describe the use case (engineer, operations, interview demo) before implementation details.
- **PRs:** link the issue when applicable; include a short summary of behavior change.

## Help wanted

Areas where contributions are especially useful (see README milestones):

- **Second catalog source** — validate CSV contract with another dataset
- **API auth** — controlled deployment for FastAPI endpoints
- **Query interpretation** — expand golden multiturn and reference resolution fixtures
- **Richer PO export** — formats beyond base CSV

## Evaluation

Frozen CI metrics and golden fixtures are documented in [`docs/contract/evaluation.md`](docs/contract/evaluation.md). CI validates contracts and formula logic; it does **not** run live Groq evals.

## Code of conduct

Be direct, precise, and respectful. Disagreements belong in issues and PR review.
