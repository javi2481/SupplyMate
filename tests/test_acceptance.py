import csv
import io

from fastapi.testclient import TestClient

from app.api import app
from app.models import AnalyticalScope
from app.query_interpretation import interpret_query_rules
from app.reference_resolver import resolve_references
from app.scope_builder import build_scope, promote_new_query_if_needed
from app.services import scope as scope_svc

client = TestClient(app)


def _scope_panales_xxg() -> AnalyticalScope:
    root_interp = interpret_query_rules("¿Cuántos pañales tengo que comprar?")
    assert root_interp is not None
    root_resolved = resolve_references(root_interp)
    root_scope = build_scope(root_interp, root_resolved, None)

    refined_interp = interpret_query_rules("me refiero a los XXG", root_scope)
    assert refined_interp is not None
    refined_resolved = resolve_references(refined_interp)
    refined_interp = promote_new_query_if_needed(
        refined_interp, refined_resolved, root_scope
    )
    return build_scope(refined_interp, refined_resolved, root_scope)


def test_acceptance_panales_xxg_slice_and_csv_match():
    scope = _scope_panales_xxg()
    assert any("Pañal" in c for c in scope.categories)
    assert "xxg" in scope.name_tokens

    params = {
        "category": scope.categories[0],
        "name_token": "xxg",
        "limit": 25,
    }
    slice_resp = client.get("/replenishment/slice", params=params)
    assert slice_resp.status_code == 200
    slice_data = slice_resp.json()
    purchase_list = slice_data["purchase_list"]

    csv_resp = client.get("/replenishment/purchase-list.csv", params=params)
    assert csv_resp.status_code == 200
    rows = list(csv.reader(io.StringIO(csv_resp.text)))
    assert len(rows) == len(purchase_list) + 1

    for item in purchase_list:
        parts = item["product_name"].lower().split()
        assert "xxg" in parts
        assert "xxxg" not in parts


def test_acceptance_scope_add_xxg_matches_pipeline():
    scope = scope_svc.add(
        scope_svc.add(AnalyticalScope(), "category", "Pañales"),
        "name_token",
        "xxg",
    )
    params = {"category": "Pañales", "name_token": "xxg", "limit": 10}
    json_items = client.get("/replenishment/purchase-list", params=params).json()
    csv_rows = list(
        csv.reader(
            io.StringIO(
                client.get("/replenishment/purchase-list.csv", params=params).text
            )
        )
    )
    assert len(csv_rows) == len(json_items) + 1
