from copy import deepcopy

from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.models import AnalyticalScope
from app.services import scope as scope_svc

_CATEGORY = st.sampled_from(["Jabon", "Pañales", "Shampoo", "Cosmetica"])
_TOKEN = st.from_regex(r"[a-z]{3,6}", fullmatch=True)


@given(value=_CATEGORY)
@settings(max_examples=50, deadline=None)
def test_add_remove_restores_cache_key(value: str):
    base = AnalyticalScope()
    key_before = scope_svc.cache_key(base)
    scoped = scope_svc.add(base, "category", value)
    restored = scope_svc.remove(scoped, "category", value)
    assert scope_svc.cache_key(restored) == key_before


@given(cat_a=_CATEGORY, cat_b=_CATEGORY)
@settings(max_examples=50, deadline=None)
def test_category_order_is_commutative_for_cache_key(cat_a: str, cat_b: str):
    scope_ab = scope_svc.add(AnalyticalScope(), "category", cat_a)
    scope_ab = scope_svc.add(scope_ab, "category", cat_b)
    scope_ba = scope_svc.add(AnalyticalScope(), "category", cat_b)
    scope_ba = scope_svc.add(scope_ba, "category", cat_a)
    assert scope_svc.cache_key(scope_ab) == scope_svc.cache_key(scope_ba)


@given(value=_TOKEN)
@settings(max_examples=50, deadline=None)
def test_invalid_dimension_is_noop(value: str):
    base = AnalyticalScope()
    unchanged = scope_svc.add(base, "not_a_dimension", value)
    assert unchanged is base
    assert scope_svc.cache_key(unchanged) == scope_svc.cache_key(base)


@given(value=_CATEGORY)
@settings(max_examples=50, deadline=None)
def test_add_does_not_mutate_input_scope(value: str):
    base = AnalyticalScope()
    snapshot = deepcopy(base)
    scope_svc.add(base, "category", value)
    assert base == snapshot
