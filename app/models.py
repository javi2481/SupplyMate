from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class Inventory(BaseModel):
    product_id: str
    current_stock: int


class SaleRecord(BaseModel):
    date: date
    units_sold: int


class SalesHistory(BaseModel):
    product_id: str
    days: int
    records: list[SaleRecord]

    @property
    def total_units_sold(self) -> int:
        return sum(r.units_sold for r in self.records)


class ReplenishmentParams(BaseModel):
    product_id: str
    lead_time_days: int
    safety_stock: int


class ReplenishmentResult(BaseModel):
    product_id: str
    average_daily_demand: float
    demand_horizon: float
    demand_lead_time: float
    stock_target: float
    current_stock: int
    recommended_quantity: int
    horizon_days: int = 7
    history_days: int = 30
    lead_time_days: int
    safety_stock: int


class ProductMaster(BaseModel):
    product_id: str
    product_name: str
    barcode: str = ""
    barcodes: list[str] = Field(default_factory=list)
    supplier: str = ""
    supplier_id: str = ""
    category: str = ""
    category_id: str = ""
    subcategory: str = ""
    subcategory_id: str = ""
    price: float | None = None
    price_offer: float | None = None
    price_discount: float | None = None
    pvp: float | None = None
    current_stock: int = 0
    min_stock: int | None = None
    max_stock: int | None = None
    reorder_point: int | None = None
    units_sold_30d: int = 0
    lead_time_days: int = 3
    safety_stock: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def below_reorder_point(self) -> bool:
        if self.reorder_point is None:
            return False
        return self.current_stock <= self.reorder_point


class ProductSearchHit(BaseModel):
    product_id: str
    product_name: str
    barcode: str = ""
    category: str = ""


class ReplenishmentRecommendation(BaseModel):
    product_id: str
    product_name: str
    calculation: ReplenishmentResult
    context: ProductContext
    recommended_quantity: int

    @classmethod
    def from_master(
        cls, master: ProductMaster, calculation: ReplenishmentResult
    ) -> ReplenishmentRecommendation:
        context = ProductContext(
            product_name=master.product_name,
            current_stock=master.current_stock,
            reorder_point=master.reorder_point,
            min_stock=master.min_stock,
            max_stock=master.max_stock,
            below_reorder_point=master.below_reorder_point,
            units_sold_30d=master.units_sold_30d,
            average_daily_demand=calculation.average_daily_demand,
            price=master.price,
            price_offer=master.price_offer,
            pvp=master.pvp,
        )
        return cls(
            product_id=master.product_id,
            product_name=master.product_name,
            calculation=calculation,
            context=context,
            recommended_quantity=calculation.recommended_quantity,
        )


class ProductContext(BaseModel):
    product_name: str
    current_stock: int
    reorder_point: int | None = None
    min_stock: int | None = None
    max_stock: int | None = None
    below_reorder_point: bool = False
    units_sold_30d: int = 0
    average_daily_demand: float = 0.0
    price: float | None = None
    price_offer: float | None = None
    pvp: float | None = None


class PurchaseListItem(BaseModel):
    product_id: str = ""
    barcode: str = ""
    product_name: str
    supplier: str = ""
    category: str = ""
    subcategory: str = ""
    current_stock: int = 0
    reorder_point: int | None = None
    below_reorder_point: bool = False
    average_daily_demand: float = 0.0
    days_of_supply: float | None = None
    health_bucket: str = ""
    recommended_quantity: int


class CategoryBar(BaseModel):
    category: str
    recommended_quantity: int
    sku_count: int = 0


class CategorySalesBar(BaseModel):
    category: str
    units_sold: int
    sku_count: int = 0


class CoverageBar(BaseModel):
    bucket: str
    sku_count: int


class InventoryDashboard(BaseModel):
    skus: int = 0
    stockout_risk: int = 0
    understock: int = 0
    overstock: int = 0
    healthy: int = 0
    avg_coverage: float | None = None
    by_category: list[CategoryBar] = Field(default_factory=list)
    by_sales: list[CategorySalesBar] = Field(default_factory=list)
    coverage: list[CoverageBar] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    mode: str = "single"
    product_id: str = ""
    product_name: str = ""
    recommended_quantity: int = 0
    calculation: ReplenishmentResult | None = None
    context: ProductContext | None = None
    purchase_list: list[PurchaseListItem] = Field(default_factory=list)
    dashboard: InventoryDashboard | None = None


class ProductNotFoundError(Exception):
    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")


@dataclass
class SupplyContext:
    product_id: Optional[str] = None
    inventory: Optional[Inventory] = None
    sales: Optional[SalesHistory] = None
    params: Optional[ReplenishmentParams] = None
    result: Optional[ReplenishmentResult] = None
    recommendation: Optional[ReplenishmentRecommendation] = None
    errors: list[str] = field(default_factory=list)

    def ready(self) -> bool:
        return (
            self.inventory is not None
            and self.sales is not None
            and self.params is not None
        )
