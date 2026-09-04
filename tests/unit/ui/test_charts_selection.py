"""Chart click selection: parse Streamlit events and bind hits to a fat mark."""

from __future__ import annotations

from ui.charts import histogram, lollipop, selection_value

_ROWS = [
    {"category": "Cuidado del Cabello", "recommended_quantity": 50000, "sku_count": 10},
    {"category": "Cremas", "recommended_quantity": 8000, "sku_count": 3},
]


def test_selection_value_list_of_dicts():
    event = {"selection": {"category_select": [{"category": "Cuidado del Cabello"}]}}
    assert (
        selection_value(event, "category", selection_name="category_select")
        == "Cuidado del Cabello"
    )


def test_selection_value_dict_of_lists():
    event = {"selection": {"category_select": {"category": ["Cuidado del Cabello"]}}}
    assert (
        selection_value(event, "category", selection_name="category_select")
        == "Cuidado del Cabello"
    )


def test_selection_value_empty_param_is_none():
    event = {"selection": {"category_select": {}}}
    assert selection_value(event, "category", selection_name="category_select") is None


def test_selection_value_reads_attribute_mapping():
    class AttrMap(dict):
        def __getattr__(self, key: str):
            try:
                return self[key]
            except KeyError as exc:
                raise AttributeError(key) from exc

    event = AttrMap(
        selection=AttrMap(category_select=[{"category": "Fragancias"}])
    )
    assert selection_value(event, "category", selection_name="category_select") == "Fragancias"


def _bound_mark_types(spec: dict, selection_name: str) -> set[str]:
    views = []
    for param in spec.get("params") or []:
        if param.get("name") == selection_name:
            views = list(param.get("views") or [])
    named = {
        layer.get("name"): layer for layer in spec.get("layer") or [] if layer.get("name")
    }
    types: set[str] = set()
    for view in views:
        mark = named.get(view, {}).get("mark")
        if isinstance(mark, str):
            types.add(mark)
        elif isinstance(mark, dict):
            types.add(str(mark.get("type") or ""))
    if not views and spec.get("mark"):
        mark = spec["mark"]
        types.add(mark if isinstance(mark, str) else str(mark.get("type") or ""))
    return types


def _selection_param(spec: dict, selection_name: str) -> dict:
    for param in spec.get("params") or []:
        if param.get("name") == selection_name:
            return param
    for layer in spec.get("layer") or []:
        for param in layer.get("params") or []:
            if param.get("name") == selection_name:
                return param
    return {}


def test_lollipop_selection_binds_to_clickable_mark_not_only_rule():
    spec = lollipop(
        _ROWS,
        "category",
        "Categoría",
        selectable_field="category",
        selection_name="category_select",
    ).to_dict()
    bound = _bound_mark_types(spec, "category_select")
    assert bound & {"rect", "circle"}
    assert "bar" not in bound
    assert bound != {"rule"}


def test_lollipop_selection_uses_nearest_false():
    spec = lollipop(
        _ROWS,
        "category",
        "Categoría",
        selectable_field="category",
        selection_name="category_select",
    ).to_dict()
    param = _selection_param(spec, "category_select")
    select = param.get("select") or {}
    assert select.get("nearest") is False
    assert select.get("type") == "point"
    assert select.get("fields") == ["category"]


def test_lollipop_selected_values_dim_non_selected():
    spec = lollipop(
        _ROWS,
        "category",
        "Categoría",
        selectable_field="category",
        selection_name="category_select",
        selected_values=["Cuidado del Cabello"],
    ).to_dict()
    payload = str(spec)
    assert "_selected" in payload or "opacity" in payload
    layers = spec.get("layer") or [spec]
    opacity_layers = [
        layer
        for layer in layers
        if isinstance((layer.get("encoding") or {}).get("opacity"), dict)
        or (
            isinstance(layer.get("mark"), dict)
            and "opacity" in (layer.get("mark") or {})
            and layer.get("mark", {}).get("type") in ("circle", "rule")
        )
    ]
    assert opacity_layers, "selected scope must encode opacity on visible marks"


def test_lollipop_includes_end_value_labels():
    spec = lollipop(
        _ROWS,
        "category",
        "Categoría",
        selectable_field="category",
        selection_name="category_select",
    ).to_dict()
    layers = spec.get("layer") or [spec]
    text_layers = []
    for layer in layers:
        mark = layer.get("mark")
        if mark == "text" or (isinstance(mark, dict) and mark.get("type") == "text"):
            text_layers.append(layer)
    assert text_layers, "lollipop must show recommended quantity labels"


def test_histogram_exposes_named_point_selection():
    spec = histogram(
        [{"bucket": "0-3", "sku_count": 4}],
        "bucket",
        "Cobertura",
        selectable_field="bucket",
        selection_name="coverage_select",
    ).to_dict()
    names = [p.get("name") for p in spec.get("params") or []]
    assert "coverage_select" in names


def test_histogram_selected_values_dim_non_selected():
    spec = histogram(
        [
            {"bucket": "0–3 días", "sku_count": 4},
            {"bucket": "3–7 días", "sku_count": 2},
        ],
        "bucket",
        "Cobertura",
        x_sort=["0–3 días", "3–7 días"],
        selectable_field="bucket",
        selection_name="coverage_select",
        selected_values=["0–3 días"],
    ).to_dict()
    encoding = spec.get("encoding") or {}
    opacity = encoding.get("opacity")
    assert opacity is not None


def test_explore_charts_use_single_brand_blue():
    from ui.theme import COVERAGE_COLORS, SHELL_TOKENS

    brand = SHELL_TOKENS["primary_accent"]
    lolli = lollipop(_ROWS, "category", "Categoría").to_dict()
    layers = lolli.get("layer") or [lolli]
    for layer in layers:
        encoding = layer.get("encoding") or {}
        color = encoding.get("color") or {}
        scale = color.get("scale") or {}
        assert scale.get("scheme") != "orangered"
        if "range" in scale:
            assert all(c == brand for c in scale["range"])
        elif color.get("value"):
            assert color["value"] == brand

    hist = histogram(
        [{"bucket": "0–3 días", "sku_count": 4}, {"bucket": "3–7 días", "sku_count": 2}],
        "bucket",
        "Cobertura",
        x_sort=["0–3 días", "3–7 días"],
    ).to_dict()
    color = (hist.get("encoding") or {}).get("color") or {}
    scale = color.get("scale") or {}
    range_ = scale.get("range") or []
    if range_:
        assert all(c == brand for c in range_)
    else:
        assert color.get("value") == brand
    assert "orangered" not in str(hist)
    # Must not paint Explore coverage with the health/coverage traffic-light palette.
    for cov_color in COVERAGE_COLORS.values():
        assert cov_color not in range_
        assert color.get("value") != cov_color or cov_color == brand
    assert range_ != [COVERAGE_COLORS.get(b, "#546E7A") for b in ["0–3 días", "3–7 días"]]
    assert COVERAGE_COLORS["0–3 días"] == "#E53935"
