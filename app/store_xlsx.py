"""Optional xlsx loader (regenerate CSVs with scripts/export_catalog_csvs.py for runtime)."""

from __future__ import annotations

from pathlib import Path

from app.models import ProductMaster
from app.store import (
    CatalogStore,
    _as_float,
    _as_int,
    _as_str,
    _index_barcodes,
    _validate_store,
)


def load_store_from_xlsx(path: Path) -> CatalogStore:
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [_as_str(h).lower() for h in next(rows)]

    def col(*names: str) -> int | None:
        for name in names:
            if name in headers:
                return headers.index(name)
        return None

    i_codigo = col("código", "codigo")
    i_name = col("artículo", "articulo")
    i_barcode = col("cód. barras", "cod. barras", "cod_barras")
    i_precio = col("precio")
    i_ofer = col("precio con ofer")
    i_dto = col("precio con dto")
    i_pvp = col("pvp")
    i_prov = col("proveedor")
    i_cod_prov = col("cod_proveedor")
    i_cat = col("categoria")
    i_cod_cat = col("cod_categoria")
    i_sub = col("subcategoria")
    i_cod_sub = col("cod_subcategoria")
    i_stock = col("stock")
    i_ventas = col("ventas_30d")
    i_lead = col("lead_time_dias", "lead_time_days")
    i_safety = col("safety_stock")
    i_min = col("minimo")
    i_max = col("maximo")
    i_quiebre = col("punto_quiebre", "punto_de_quiebre")
    barcode_cols = [
        i
        for i, h in enumerate(headers)
        if h.startswith("codigobarras") or h in {"cód. barras", "cod. barras"}
    ]

    if i_codigo is None or i_name is None:
        wb.close()
        raise ValueError(f"Catalog xlsx missing Código/Artículo columns: {path}")

    store = CatalogStore(source=str(path))
    for raw in rows:
        vals = list(raw)
        if not vals or all(v is None or v == "" for v in vals):
            continue
        product_id = _as_str(vals[i_codigo])
        name = _as_str(vals[i_name])
        if not product_id or not name:
            continue

        codes: list[str] = []
        if i_barcode is not None:
            codes.append(_as_str(vals[i_barcode]))
        for bi in barcode_cols:
            if bi < len(vals):
                codes.append(_as_str(vals[bi]))
        codes = [c for c in codes if c]

        master = ProductMaster(
            product_id=product_id,
            product_name=name,
            barcode=codes[0] if codes else "",
            barcodes=list(dict.fromkeys(codes)),
            supplier=_as_str(vals[i_prov]) if i_prov is not None else "",
            supplier_id=_as_str(vals[i_cod_prov]) if i_cod_prov is not None else "",
            category=_as_str(vals[i_cat]) if i_cat is not None else "",
            category_id=_as_str(vals[i_cod_cat]) if i_cod_cat is not None else "",
            subcategory=_as_str(vals[i_sub]) if i_sub is not None else "",
            subcategory_id=_as_str(vals[i_cod_sub]) if i_cod_sub is not None else "",
            price=_as_float(vals[i_precio]) if i_precio is not None else None,
            price_offer=_as_float(vals[i_ofer]) if i_ofer is not None else None,
            price_discount=_as_float(vals[i_dto]) if i_dto is not None else None,
            pvp=_as_float(vals[i_pvp]) if i_pvp is not None else None,
            current_stock=_as_int(vals[i_stock]) if i_stock is not None else 0,
            min_stock=_as_int(vals[i_min]) if i_min is not None else None,
            max_stock=_as_int(vals[i_max]) if i_max is not None else None,
            reorder_point=_as_int(vals[i_quiebre]) if i_quiebre is not None else None,
            units_sold_30d=_as_int(vals[i_ventas]) if i_ventas is not None else 0,
            lead_time_days=_as_int(vals[i_lead], 3) if i_lead is not None else 3,
            safety_stock=_as_int(vals[i_safety]) if i_safety is not None else 0,
        )
        store.products[product_id] = master
        _index_barcodes(store, product_id, master.barcodes)

    wb.close()
    _validate_store(store)
    return store
