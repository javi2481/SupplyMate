from app.core.models import AnalyticalScope
from app.services import panel_modes


def test_can_export_only_in_commit():
    assert panel_modes.can_export("explore") is False
    assert panel_modes.can_export("commit") is True


def test_effective_scope_commit_requires_frozen():
    scope = AnalyticalScope(categories=["Perfumería"])
    try:
        panel_modes.effective_scope("commit", scope, None)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "frozen_scope" in str(exc)


def test_effective_scope_commit_uses_frozen():
    scope = AnalyticalScope(categories=["A"])
    frozen = AnalyticalScope(categories=["A"], highlight_product_id="123")
    effective = panel_modes.effective_scope("commit", scope, frozen)
    assert effective.highlight_product_id == "123"


def test_validate_commit_mismatch_filters():
    scope = AnalyticalScope(categories=["A"])
    frozen = AnalyticalScope(categories=["B"])
    try:
        panel_modes.validate_commit_request("commit", scope, frozen)
        assert False
    except ValueError as exc:
        assert "must match" in str(exc)
