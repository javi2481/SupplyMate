from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from app import config
from app.models import (
    Inventory,
    ProductMaster,
    ProductNotFoundError,
    ProductSearchHit,
    ReplenishmentParams,
    SaleRecord,
    SalesHistory,
)

logger = logging.getLogger(__name__)

HISTORY_DAYS = 30
SALES_AS_OF = date(2026, 8, 25)


@dataclass
class CatalogStore:
    """In-memory simulated catalog API backed by resource CSVs."""

    products: dict[str, ProductMaster] = field(default_factory=dict)
    barcode_index: dict[str, str] = field(default_factory=dict)
    source: str = ""
    boot_warnings: list[str] = field(default_factory=list)

    def list_products(self) -> list[dict[str, str]]:
        return [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "barcode": p.barcode,
            }
            for p in self.products.values()
        ]

    def get(self, product_id: str) -> ProductMaster:
        row = self.products.get(product_id)
        if row is None:
            raise ProductNotFoundError(product_id)
        return row

    def get_master(self, product_id: str) -> ProductMaster:
        return self.get(product_id)

    def resolve_exact(self, query: str) -> str | None:
        raw = query.strip()
        if not raw:
            return None
        if raw in self.products:
            return raw
        upper = raw.upper()
        for pid in self.products:
            if pid.upper() == upper:
                return pid
        digits = "".join(c for c in raw if c.isdigit())
        if digits and digits in self.products:
            return digits
        if digits and digits in self.barcode_index:
            return self.barcode_index[digits]
        if raw in self.barcode_index:
            return self.barcode_index[raw]
        return None

    def search(self, query: str, limit: int = 10) -> list[ProductSearchHit]:
        q = query.strip().lower()
        if not q:
            return []

        exact = self.resolve_exact(query)
        if exact:
            master = self.get(exact)
            return [
                ProductSearchHit(
                    product_id=master.product_id,
                    product_name=master.product_name,
                    barcode=master.barcode,
                    category=master.category,
                )
            ]

        hits: list[tuple[int, ProductSearchHit]] = []
        for master in self.products.values():
            name = master.product_name.lower()
            score = 0
            if q in name:
                score = 80 + min(len(q), 15)
            elif any(t in q for t in name.split() if len(t) >= 4):
                score = 50
            if score:
                hits.append(
                    (
                        score,
                        ProductSearchHit(
                            product_id=master.product_id,
                            product_name=master.product_name,
                            barcode=master.barcode,
                            category=master.category,
                        ),
                    )
                )
        hits.sort(key=lambda item: (-item[0], item[1].product_id))
        return [hit for _, hit in hits[:limit]]

    def inventory(self, product_id: str) -> Inventory:
        row = self.get(product_id)
        return Inventory(product_id=row.product_id, current_stock=row.current_stock)

    def params(self, product_id: str) -> ReplenishmentParams:
        row = self.get(product_id)
        return ReplenishmentParams(
            product_id=row.product_id,
            lead_time_days=row.lead_time_days,
            safety_stock=row.safety_stock,
        )

    def sales_history(
        self,
        product_id: str,
        days: int = HISTORY_DAYS,
        as_of: date | None = None,
    ) -> SalesHistory:
        row = self.get(product_id)
        as_of = as_of or SALES_AS_OF
        records = _expand_sales(row.units_sold_30d, days=days, as_of=as_of)
        return SalesHistory(product_id=row.product_id, days=days, records=records)


def _as_int(value: object, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if text.endswith(".0") and text.replace(".", "", 1).isdigit():
        return text[:-2]
    return text


def _expand_sales(total: int, days: int, as_of: date) -> list[SaleRecord]:
    total = max(0, int(total))
    days = max(1, int(days))
    base, rem = divmod(total, days)
    records: list[SaleRecord] = []
    start = as_of - timedelta(days=days - 1)
    for i in range(days):
        units = base + (1 if i < rem else 0)
        records.append(SaleRecord(date=start + timedelta(days=i), units_sold=units))
    return records


def _index_barcodes(store: CatalogStore, product_id: str, codes: list[str]) -> None:
    for code in codes:
        code = _as_str(code)
        if code and code not in store.barcode_index:
            store.barcode_index[code] = product_id


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _optional_int(row: dict[str, str], key: str) -> int | None:
    val = row.get(key)
    if val in (None, ""):
        return None
    return _as_int(val)


def _build_master(
    p: dict[str, str],
    inv: dict[str, str],
    price_row: dict[str, str],
    lt: int,
    ss: int,
    units_sold: int,
) -> ProductMaster:
    codes = [
        _as_str(p.get(k, ""))
        for k in ("barcode", "barcode_2", "barcode_3", "barcode_4", "barcode_5")
    ]
    codes = [c for c in codes if c]
    primary = codes[0] if codes else ""
    return ProductMaster(
        product_id=p["product_id"],
        product_name=p["product_name"],
        barcode=primary,
        barcodes=list(dict.fromkeys(codes)),
        supplier=_as_str(p.get("supplier", "")),
        supplier_id=_as_str(p.get("supplier_id", "")),
        category=_as_str(p.get("category", "")),
        category_id=_as_str(p.get("category_id", "")),
        subcategory=_as_str(p.get("subcategory", "")),
        subcategory_id=_as_str(p.get("subcategory_id", "")),
        price=_as_float(price_row.get("price")),
        price_offer=_as_float(price_row.get("price_offer")),
        price_discount=_as_float(price_row.get("price_discount")),
        pvp=_as_float(price_row.get("pvp")),
        current_stock=_as_int(inv.get("current_stock", 0)),
        min_stock=_optional_int(inv, "min_stock"),
        max_stock=_optional_int(inv, "max_stock"),
        reorder_point=_optional_int(inv, "reorder_point"),
        units_sold_30d=units_sold,
        lead_time_days=lt,
        safety_stock=ss,
    )


def _validate_store(store: CatalogStore) -> None:
    n = len(store.products)
    if n == 0:
        store.boot_warnings.append("Catalog is empty")
        return
    bad_prices = sum(
        1 for p in store.products.values() if p.price is not None and p.price <= 0.01
    )
    if bad_prices:
        msg = f"{bad_prices} products with price <= 0.01"
        store.boot_warnings.append(msg)
        logger.warning(msg)
    logger.info("Catalog loaded: %s SKUs from %s", n, store.source)


def load_store_from_csvs(data_dir: Path | None = None) -> CatalogStore:
    """Load resource CSVs from data_dir (API-shaped split)."""
    data_dir = data_dir or config.DATA_DIR
    products_csv = data_dir / "products.csv"
    inventory_csv = data_dir / "inventory.csv"
    params_csv = data_dir / "replenishment_params.csv"
    prices_csv = data_dir / "prices.csv"
    sales_csv = data_dir / "sales_summary.csv"
    if not sales_csv.exists():
        sales_csv = data_dir / "sales_history.csv"
    if not sales_csv.exists():
        raise FileNotFoundError(
            f"Missing sales CSV (sales_summary.csv or sales_history.csv) in {data_dir}"
        )

    products = _read_csv(products_csv)
    inventory_rows = {r["product_id"]: r for r in _read_csv(inventory_csv)}
    params = {
        r["product_id"]: (
            _as_int(r["lead_time_days"], 3),
            _as_int(r["safety_stock"]),
        )
        for r in _read_csv(params_csv)
    }
    prices_rows: dict[str, dict[str, str]] = {}
    if prices_csv.exists():
        prices_rows = {r["product_id"]: r for r in _read_csv(prices_csv)}
    sales_totals: dict[str, int] = {}
    for r in _read_csv(sales_csv):
        sales_totals[r["product_id"]] = sales_totals.get(r["product_id"], 0) + _as_int(
            r["units_sold"]
        )

    store = CatalogStore(source=str(data_dir))
    for p in products:
        pid = p["product_id"]
        inv = inventory_rows.get(pid, {})
        lt, ss = params.get(pid, (3, 0))
        price_row = prices_rows.get(pid, {})
        master = _build_master(p, inv, price_row, lt, ss, sales_totals.get(pid, 0))
        store.products[pid] = master
        _index_barcodes(store, pid, master.barcodes)

    _validate_store(store)
    return store


def reset_store_cache() -> None:
    get_store.cache_clear()


@lru_cache(maxsize=1)
def get_store() -> CatalogStore:
    if config.PRODUCTS_CSV.exists():
        return load_store_from_csvs(config.DATA_DIR)
    xlsx = config.CATALOG_XLSX
    if xlsx is not None and xlsx.exists():
        from app.store_xlsx import load_store_from_xlsx

        return load_store_from_xlsx(xlsx)
    raise FileNotFoundError(
        f"No catalog found under {config.DATA_DIR} and no xlsx at {xlsx}"
    )
