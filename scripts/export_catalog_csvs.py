"""Split docs/perfumeria_enriched.xlsx into resource-oriented CSVs under data/.

Mirrors a typical simulated API layout:
  GET /products
  GET /prices
  GET /inventory
  GET /sales/summary
  GET /replenishment-params
"""

from __future__ import annotations

import csv
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "docs" / "perfumeria_enriched.xlsx"
OUT = ROOT / "data"


def _as_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if text.endswith(".0") and text.replace(".", "", 1).isdigit():
        return text[:-2]
    return text


def _as_num(value: object) -> str:
    if value is None or value == "":
        return ""
    try:
        f = float(value)
        if f.is_integer():
            return str(int(f))
        return f"{f:.4f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return _as_str(value)


def _write(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  {path.name}: {len(rows)} rows")


def main() -> None:
    if not XLSX.exists():
        raise SystemExit(f"Missing source xlsx: {XLSX}")

    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb.active
    it = ws.iter_rows(values_only=True)
    headers = [_as_str(h) for h in next(it)]
    # Normalize lookup keys
    idx = {h.lower(): i for i, h in enumerate(headers)}

    def col(*names: str) -> int | None:
        for n in names:
            if n.lower() in idx:
                return idx[n.lower()]
        return None

    i_codigo = col("Código", "Codigo")
    i_name = col("Artículo", "Articulo")
    i_barcode = col("Cód. barras", "Cod. barras")
    i_precio = col("Precio")
    i_ofer = col("Precio con ofer")
    i_dto = col("Precio con dto")
    i_pvp = col("PVP")
    i_prov = col("Proveedor")
    i_cod_prov = col("cod_proveedor")
    i_cat = col("categoria")
    i_cod_cat = col("cod_categoria")
    i_sub = col("subcategoria")
    i_cod_sub = col("cod_subcategoria")
    i_cb = [col(f"codigobarras{n}") for n in range(1, 6)]
    i_min = col("minimo")
    i_max = col("maximo")
    i_quiebre = col("punto_quiebre")
    i_stock = col("stock")
    i_ventas = col("ventas_30d")
    i_lead = col("lead_time_dias")
    i_safety = col("safety_stock")

    if i_codigo is None or i_name is None:
        raise SystemExit(f"Unexpected headers: {headers}")

    products: list[dict[str, str]] = []
    prices: list[dict[str, str]] = []
    inventory: list[dict[str, str]] = []
    sales: list[dict[str, str]] = []
    params: list[dict[str, str]] = []

    for raw in it:
        vals = list(raw)
        if not vals:
            continue
        pid = _as_str(vals[i_codigo])
        name = _as_str(vals[i_name])
        if not pid or not name:
            continue

        barcodes = []
        if i_barcode is not None:
            barcodes.append(_as_str(vals[i_barcode]))
        for bi in i_cb:
            if bi is not None and bi < len(vals):
                barcodes.append(_as_str(vals[bi]))
        barcodes = list(dict.fromkeys(c for c in barcodes if c))
        primary = barcodes[0] if barcodes else ""

        products.append(
            {
                "product_id": pid,
                "product_name": name,
                "barcode": primary,
                "barcode_2": barcodes[1] if len(barcodes) > 1 else "",
                "barcode_3": barcodes[2] if len(barcodes) > 2 else "",
                "barcode_4": barcodes[3] if len(barcodes) > 3 else "",
                "barcode_5": barcodes[4] if len(barcodes) > 4 else "",
                "supplier": _as_str(vals[i_prov]) if i_prov is not None else "",
                "supplier_id": _as_str(vals[i_cod_prov]) if i_cod_prov is not None else "",
                "category": _as_str(vals[i_cat]) if i_cat is not None else "",
                "category_id": _as_str(vals[i_cod_cat]) if i_cod_cat is not None else "",
                "subcategory": _as_str(vals[i_sub]) if i_sub is not None else "",
                "subcategory_id": _as_str(vals[i_cod_sub]) if i_cod_sub is not None else "",
            }
        )
        prices.append(
            {
                "product_id": pid,
                "price": _as_num(vals[i_precio]) if i_precio is not None else "",
                "price_offer": _as_num(vals[i_ofer]) if i_ofer is not None else "",
                "price_discount": _as_num(vals[i_dto]) if i_dto is not None else "",
                "pvp": _as_num(vals[i_pvp]) if i_pvp is not None else "",
            }
        )
        inventory.append(
            {
                "product_id": pid,
                "current_stock": _as_num(vals[i_stock]) if i_stock is not None else "0",
                "min_stock": _as_num(vals[i_min]) if i_min is not None else "",
                "max_stock": _as_num(vals[i_max]) if i_max is not None else "",
                "reorder_point": _as_num(vals[i_quiebre]) if i_quiebre is not None else "",
            }
        )
        sales.append(
            {
                "product_id": pid,
                "days": "30",
                "units_sold": _as_num(vals[i_ventas]) if i_ventas is not None else "0",
                "period_end": "2026-08-25",
            }
        )
        params.append(
            {
                "product_id": pid,
                "lead_time_days": _as_num(vals[i_lead]) if i_lead is not None else "3",
                "safety_stock": _as_num(vals[i_safety]) if i_safety is not None else "0",
            }
        )

    wb.close()

    # Remove legacy wide sales_history if present (replaced by sales_summary).
    legacy = OUT / "sales_history.csv"
    if legacy.exists():
        legacy.unlink()

    print(f"Exporting from {XLSX.name} -> {OUT}/")
    _write(
        OUT / "products.csv",
        [
            "product_id",
            "product_name",
            "barcode",
            "barcode_2",
            "barcode_3",
            "barcode_4",
            "barcode_5",
            "supplier",
            "supplier_id",
            "category",
            "category_id",
            "subcategory",
            "subcategory_id",
        ],
        products,
    )
    _write(
        OUT / "prices.csv",
        ["product_id", "price", "price_offer", "price_discount", "pvp"],
        prices,
    )
    _write(
        OUT / "inventory.csv",
        ["product_id", "current_stock", "min_stock", "max_stock", "reorder_point"],
        inventory,
    )
    _write(
        OUT / "sales_summary.csv",
        ["product_id", "days", "units_sold", "period_end"],
        sales,
    )
    _write(
        OUT / "replenishment_params.csv",
        ["product_id", "lead_time_days", "safety_stock"],
        params,
    )
    print("done")


if __name__ == "__main__":
    main()
