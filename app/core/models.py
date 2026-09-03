from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, computed_field

PanelMode = Literal["explore", "commit"]

BusinessIntent = Literal[
    "replenishment",
    "inventory_risk",
    "sales_ranking",
    "single_sku",
    "unknown",
]

QueryRelation = Literal["new_query", "refinement"]
GuidanceAction = Literal[
    "show_analysis", "ask_clarification", "refine_analysis", "draft_oc"
]
ReferenceKind = Literal["product_group", "sku_hint", "filter_hint"]
MatchKind = Literal["exact_sku", "group", "ambiguous", "unresolved"]
ScopeDimension = Literal["category", "subcategory", "sku_set"]
ConfidenceLevel = Literal["high", "low"]


class GuidanceChip(BaseModel):
    label: str
    action: str
    args: dict[str, str] = Field(default_factory=dict)
    caption: str = ""
    preview_skus: int = 0
    preview_qty: int = 0
    preview_value: float | None = None


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=2000)
    scope: Optional["AnalyticalScope"] = None
    chip: Optional[GuidanceChip] = None
    confirm_union: bool = False


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
    operational_priority: str = "normal"
    purchase_cost: float | None = None
    estimated_purchase_value: float | None = None


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
    estimated_purchase_value: float | None = None
    by_category: list[CategoryBar] = Field(default_factory=list)
    by_sales: list[CategorySalesBar] = Field(default_factory=list)
    coverage: list[CoverageBar] = Field(default_factory=list)


class AnalyticalScope(BaseModel):
    categories: list[str] = Field(default_factory=list)
    subcategories: list[str] = Field(default_factory=list)
    coverage_buckets: list[str] = Field(default_factory=list)
    health_buckets: list[str] = Field(default_factory=list)
    suppliers: list[str] = Field(default_factory=list)
    name_tokens: list[str] = Field(default_factory=list)
    guidance_dismissed: list[str] = Field(default_factory=list)
    highlight_product_id: str = ""


class Reference(BaseModel):
    text: str = Field(max_length=80)
    kind: ReferenceKind = "product_group"


class QueryInterpretation(BaseModel):
    intent: BusinessIntent = "unknown"
    references: list[Reference] = Field(default_factory=list, max_length=5)
    filter_hints: list[str] = Field(default_factory=list, max_length=5)
    confidence: ConfidenceLevel = "high"
    source: Literal["rules", "llm", "hybrid"] = "rules"
    relation: QueryRelation = "new_query"


class ResolvedReference(BaseModel):
    label: str = ""
    user_text: str = ""
    match_kind: MatchKind = "unresolved"
    product_id: str = ""
    sku_ids: list[str] = Field(default_factory=list)
    scope_dimension: ScopeDimension = "category"
    scope_value: str = ""
    name_tokens: list[str] = Field(default_factory=list)
    sku_count: int = 0
    recommended_quantity: int = 0
    confidence: ConfidenceLevel = "high"


class ResolutionResult(BaseModel):
    interpretation: QueryInterpretation
    resolved: list[ResolvedReference] = Field(default_factory=list)
    scope: AnalyticalScope = Field(default_factory=AnalyticalScope)
    disambiguation_options: list[str] = Field(default_factory=list)
    blocking: bool = False


class GroupSummary(BaseModel):
    label: str
    recommended_quantity: int
    sku_count: int = 0


class ChatInterpretation(BaseModel):
    understood_labels: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = "high"
    relation: QueryRelation = "new_query"
    disambiguation_question: str = ""
    disambiguation_options: list[str] = Field(default_factory=list)
    guidance_question: str = ""
    guidance_options: list[str] = Field(default_factory=list)


class GuidanceDecision(BaseModel):
    action: GuidanceAction = "show_analysis"
    reason: str = ""
    question: str = ""
    options: list[str] = Field(default_factory=list)
    chips: list[GuidanceChip] = Field(default_factory=list)
    progress_label: str = ""
    progress_step: int = 0
    progress_total: int = 0
    reference: str = ""


class SuggestedFilter(BaseModel):
    action: str
    args: dict[str, str] = Field(default_factory=dict)
    label: str


class ReplenishmentSlice(BaseModel):
    scope: AnalyticalScope
    evidence: str
    dashboard: InventoryDashboard
    purchase_list: list[PurchaseListItem] = Field(default_factory=list)
    suggested_filters: list[SuggestedFilter] = Field(default_factory=list)
    guidance: GuidanceDecision | None = None


class InteractionEvent(BaseModel):
    source: Literal[
        "chart_category",
        "chart_coverage",
        "table_row",
        "chip",
        "breadcrumb",
        "reset",
        "chat",
        "mode_transition",
    ]
    action: Literal[
        "add_filter",
        "remove_filter",
        "highlight_sku",
        "reset",
        "enter_commit",
        "exit_commit",
    ]
    dimension: str = ""
    value: str = ""
    label_human: str = ""


class PurchasePriority(BaseModel):
    product_id: str
    product_name: str
    recommended_quantity: int
    reason: str = Field(max_length=200)


class DashboardInsight(BaseModel):
    panel_title: str = ""
    summary: str = ""
    bullets: list[str] = Field(default_factory=list, max_length=5)
    purchase_priorities: list[PurchasePriority] = Field(default_factory=list, max_length=5)
    navigation_hints: list[str] = Field(default_factory=list, max_length=4)
    suggested_questions: list[str] = Field(default_factory=list, max_length=3)
    highlight_kpis: list[str] = Field(default_factory=list)


class CommitSummary(BaseModel):
    headline: str = ""
    oc_summary: str = ""
    top_priorities: list[PurchasePriority] = Field(default_factory=list, max_length=3)
    checklist: list[str] = Field(default_factory=list, max_length=4)


class AnalyzeRequest(BaseModel):
    mode: PanelMode = "explore"
    scope: AnalyticalScope
    frozen_scope: AnalyticalScope | None = None
    events: list[InteractionEvent] = Field(default_factory=list, max_length=50)
    root_question: str = Field(default="", max_length=500)
    insight_level: Literal["lite", "full"] = "full"


class AnalyzeResponse(BaseModel):
    mode: PanelMode
    scope: AnalyticalScope
    frozen_scope: AnalyticalScope | None = None
    evidence: str
    dashboard: InventoryDashboard
    purchase_list: list[PurchaseListItem] = Field(default_factory=list)
    insight: DashboardInsight | None = None
    commit_summary: CommitSummary | None = None
    insight_source: Literal["llm", "fallback"]
    compiled_prompt_hash: str = ""


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
    scope: AnalyticalScope | None = None
    interpretation: ChatInterpretation | None = None
    group_summaries: list[GroupSummary] = Field(default_factory=list)
    guidance: GuidanceDecision | None = None


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
