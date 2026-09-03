#!/usr/bin/env python3
"""Bulk-update imports after app/ package reorganization."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPLACEMENTS: list[tuple[str, str]] = [
    ("app.services.catalog_service", "app.services.analytics.catalog_service"),
    ("app.services.dashboard", "app.services.analytics.dashboard"),
    ("app.services.metrics", "app.services.analytics.metrics"),
    ("app.services.scope_sanitize", "app.services.scope.scope_sanitize"),
    ("app.services.panel_modes", "app.services.scope.panel_modes"),
    ("app.services.suggested_filters", "app.services.scope.suggested_filters"),
    ("app.services.insight_validator", "app.services.insight.insight_validator"),
    ("app.services.insight_cache", "app.services.insight.insight_cache"),
    ("app.services.prompt_compiler", "app.services.insight.prompt_compiler"),
    ("app.services.scope", "app.services.scope.scope"),
    ("app.query_interpreter_agent", "app.pipeline.query_interpreter_agent"),
    ("app.query_interpretation", "app.pipeline.query_interpretation"),
    ("app.reference_resolver", "app.pipeline.reference_resolver"),
    ("app.scope_builder", "app.pipeline.scope_builder"),
    ("app.guidance_chips", "app.guidance.guidance_chips"),
    ("app.guidance_tokens", "app.guidance.guidance_tokens"),
    ("app.slice_facets", "app.guidance.slice_facets"),
    ("app.missions", "app.guidance.missions"),
    ("app.explore_answer", "app.agent.explore_answer"),
    ("app.intent_classifier", "app.agent.intent_classifier"),
    ("app.replenishment", "app.core.replenishment"),
    ("app.store_xlsx", "app.catalog.store_xlsx"),
    ("app.products", "app.catalog.products"),
    ("app.llm_log", "app.agent.llm_log"),
    ("app.models", "app.core.models"),
    ("app.config", "app.core.config"),
    ("app.store", "app.catalog.store"),
    ("app.intents", "app.agent.intents"),
    ("app.tools", "app.agent.tools"),
]

DOC_REPLACEMENTS: list[tuple[str, str]] = [
    ("docs/architecture.md", "docs/contract/architecture.md"),
    ("docs/architecture.es.md", "docs/contract/architecture.es.md"),
    ("docs/evaluation.md", "docs/contract/evaluation.md"),
    ("docs/evaluation.es.md", "docs/contract/evaluation.es.md"),
    ("docs/data-contract.md", "docs/contract/data-contract.md"),
    ("docs/data-contract.es.md", "docs/contract/data-contract.es.md"),
    ("docs/maintenance-policy.md", "docs/operations/maintenance-policy.md"),
    ("docs/performance-profile.md", "docs/operations/performance-profile.md"),
    ("docs/security-audit-osstmm-lite.md", "docs/operations/security-audit-osstmm-lite.md"),
    ("docs/security-deps.md", "docs/operations/security-deps.md"),
    ("docs/compatibility-matrix.md", "docs/operations/compatibility-matrix.md"),
    ("docs/beta-test-protocol.md", "docs/operations/beta-test-protocol.md"),
    ("docs/change-request-template.md", "docs/templates/change-request-template.md"),
    ("app/replenishment.py", "app/core/replenishment.py"),
    ("app/models.py", "app/core/models.py"),
    ("app/tools.py", "app/agent/tools.py"),
    ("app/agent.py", "app/agent/runner.py"),
    ("app/services/catalog_service.py", "app/services/analytics/catalog_service.py"),
    ("app/services/dashboard.py", "app/services/analytics/dashboard.py"),
    ("app/services/scope.py", "app/services/scope/scope.py"),
    ("app/query_interpretation.py", "app/pipeline/query_interpretation.py"),
    ("app/reference_resolver.py", "app/pipeline/reference_resolver.py"),
    ("app/guidance.py", "app/guidance/engine.py"),
    ("tests/test_performance.py", "tests/performance/test_performance.py"),
    ("tests/test_security.py", "tests/security/test_security.py"),
]


def apply_replacements(text: str, pairs: list[tuple[str, str]]) -> str:
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def fix_patches(text: str) -> str:
    text = text.replace('patch("app.agent.Runner.run', 'patch("app.agent.runner.Runner.run')
    text = text.replace('patch("app.agent.classify_intent', 'patch("app.agent.runner.classify_intent')
    text = text.replace('patch("app.agent.get_model', 'patch("app.agent.model.get_model')
    text = text.replace('patch("app.agent.runner.get_model', 'patch("app.agent.model.get_model')
    text = text.replace(
        'patch("app.intent_classifier.Runner.run',
        'patch("app.agent.intent_classifier.Runner.run',
    )
    return text


def fix_scope_double(text: str) -> str:
    return text.replace("app.services.scope.scope.scope", "app.services.scope.scope")


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = original
    if path.suffix == ".py":
        updated = apply_replacements(updated, REPLACEMENTS)
        updated = fix_patches(updated)
        updated = fix_scope_double(updated)
    elif path.suffix in {".md", ".toml", ".yml", ".yaml"}:
        updated = apply_replacements(updated, DOC_REPLACEMENTS)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    for pattern in ("**/*.py", "**/*.md", "pyproject.toml", ".github/**/*.yml"):
        for path in ROOT.glob(pattern):
            if any(part in {".git", "graphify-out", ".hypothesis", "supplymate.egg-info", "scripts"} for part in path.parts):
                continue
            if path.name == "migrate_imports.py":
                continue
            if process_file(path):
                changed += 1
                print(f"updated {path.relative_to(ROOT)}")
    print(f"done: {changed} files")


if __name__ == "__main__":
    main()
