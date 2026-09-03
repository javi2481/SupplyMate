import math

from hypothesis import given, settings
from hypothesis import strategies as st

from app.replenishment import calculate_replenishment

_STOCK = st.integers(min_value=0, max_value=50_000)
_SALES = st.integers(min_value=0, max_value=300_000)
_LEAD = st.integers(min_value=1, max_value=30)
_SAFETY = st.integers(min_value=0, max_value=5_000)


@given(current_stock=_STOCK, sales=_SALES, lead_time=_LEAD, safety=_SAFETY)
@settings(max_examples=200, deadline=None)
def test_recommended_quantity_is_non_negative(
    current_stock: int, sales: int, lead_time: int, safety: int
):
    result = calculate_replenishment(
        product_id="PROP",
        current_stock=current_stock,
        total_units_sold_last_30=sales,
        lead_time_days=lead_time,
        safety_stock=safety,
    )
    assert result.recommended_quantity >= 0


@given(
    base_stock=_STOCK,
    extra_stock=st.integers(min_value=1, max_value=10_000),
    sales=_SALES,
    lead_time=_LEAD,
    safety=_SAFETY,
)
@settings(max_examples=200, deadline=None)
def test_higher_stock_never_increases_recommended_quantity(
    base_stock: int, extra_stock: int, sales: int, lead_time: int, safety: int
):
    low = calculate_replenishment(
        product_id="PROP",
        current_stock=base_stock,
        total_units_sold_last_30=sales,
        lead_time_days=lead_time,
        safety_stock=safety,
    )
    high = calculate_replenishment(
        product_id="PROP",
        current_stock=base_stock + extra_stock,
        total_units_sold_last_30=sales,
        lead_time_days=lead_time,
        safety_stock=safety,
    )
    assert high.recommended_quantity <= low.recommended_quantity


@given(current_stock=_STOCK, sales=_SALES, lead_time=_LEAD, safety=_SAFETY)
@settings(max_examples=200, deadline=None)
def test_positive_gap_uses_ceil(
    current_stock: int, sales: int, lead_time: int, safety: int
):
    result = calculate_replenishment(
        product_id="PROP",
        current_stock=current_stock,
        total_units_sold_last_30=sales,
        lead_time_days=lead_time,
        safety_stock=safety,
    )
    gap = result.stock_target - current_stock
    if gap > 0:
        assert result.recommended_quantity == math.ceil(gap)
    else:
        assert result.recommended_quantity == 0
