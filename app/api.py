from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query, Response

from app.agent import run_analyze, run_supplymate
from app.config import MAX_SCOPE_VALUE_LENGTH
from app.middleware.chat_rate_limit import ChatRateLimitMiddleware
from app.middleware.safe_errors import SafeErrorMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyticalScope,
    ChatRequest,
    ChatResponse,
    InventoryDashboard,
    ProductMaster,
    ProductNotFoundError,
    ProductSearchHit,
    PurchaseListItem,
    ReplenishmentRecommendation,
    ReplenishmentSlice,
)
from app.services import catalog_service
from app.services import panel_modes
from app.services import scope as scope_svc
from app.services.scope_sanitize import sanitize_value, sanitize_values

app = FastAPI(title="SupplyMate", version="0.5.0")
app.add_middleware(ChatRateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SafeErrorMiddleware)


def _validate_scope_values(raw_values: list[str], param_name: str) -> list[str]:
    for raw in raw_values:
        if len(raw.strip()) > MAX_SCOPE_VALUE_LENGTH:
            raise HTTPException(
                status_code=422,
                detail=f"{param_name} value exceeds maximum length",
            )
    return sanitize_values(raw_values)


def _scope_dependency(
    category: list[str] = Query(default=[]),
    subcategory: list[str] = Query(default=[]),
    coverage_bucket: list[str] = Query(default=[]),
    health_bucket: list[str] = Query(default=[]),
    supplier: list[str] = Query(default=[]),
    name_token: list[str] = Query(default=[]),
    highlight_product_id: str = Query(default=""),
) -> AnalyticalScope:
    highlight = highlight_product_id or ""
    if len(highlight.strip()) > MAX_SCOPE_VALUE_LENGTH:
        raise HTTPException(
            status_code=422,
            detail="highlight_product_id exceeds maximum length",
        )
    return scope_svc.scope_from_query_params(
        categories=_validate_scope_values(category, "category"),
        subcategories=_validate_scope_values(subcategory, "subcategory"),
        coverage_buckets=_validate_scope_values(coverage_bucket, "coverage_bucket"),
        health_buckets=_validate_scope_values(health_bucket, "health_bucket"),
        suppliers=_validate_scope_values(supplier, "supplier"),
        name_tokens=_validate_scope_values(name_token, "name_token"),
        highlight_product_id=sanitize_value(highlight) or "",
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products/search", response_model=list[ProductSearchHit])
async def search_products(q: str = Query(min_length=1)) -> list[ProductSearchHit]:
    return catalog_service.search_products(q)


@app.get("/products/{product_id}", response_model=ProductMaster)
async def get_product(product_id: str) -> ProductMaster:
    try:
        return catalog_service.get_master(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/products/{product_id}/replenishment", response_model=ReplenishmentRecommendation)
async def get_replenishment(product_id: str) -> ReplenishmentRecommendation:
    try:
        return catalog_service.get_replenishment_recommendation(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/replenishment/slice", response_model=ReplenishmentSlice)
async def replenishment_slice(
    scope: AnalyticalScope = Depends(_scope_dependency),
    limit: int = Query(default=25, ge=1, le=100),
) -> ReplenishmentSlice:
    return catalog_service.replenishment_slice(scope, limit=limit)


@app.get("/replenishment/dashboard", response_model=InventoryDashboard)
async def inventory_dashboard(
    scope: AnalyticalScope = Depends(_scope_dependency),
) -> InventoryDashboard:
    snap, _items = catalog_service.chat_dashboard(limit=1, scope=scope)
    return snap


@app.get("/replenishment/purchase-list", response_model=list[PurchaseListItem])
async def purchase_list(
    scope: AnalyticalScope = Depends(_scope_dependency),
    limit: int = Query(default=25, ge=1, le=100),
) -> list[PurchaseListItem]:
    _snap, items = catalog_service.chat_dashboard(limit=limit, scope=scope)
    return items


@app.get("/replenishment/purchase-list.csv")
async def purchase_list_csv(
    scope: AnalyticalScope = Depends(_scope_dependency),
    limit: int = Query(default=25, ge=1, le=100),
) -> Response:
    body = catalog_service.purchase_list_csv(limit=limit, scope=scope)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=purchase_order.csv"},
    )


@app.post("/replenishment/analyze", response_model=AnalyzeResponse)
async def replenishment_analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    try:
        panel_modes.validate_commit_request(
            body.mode, body.scope, body.frozen_scope
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        return await run_analyze(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.chip and not (request.message or "").strip():
        raise HTTPException(status_code=422, detail="message or chip is required")
    try:
        return await run_supplymate(
            request.message,
            request.scope,
            chip=request.chip,
        )
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
