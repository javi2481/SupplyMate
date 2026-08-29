from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app.agent import run_supplymate
from app.models import (
    ChatRequest,
    ChatResponse,
    ProductMaster,
    ProductNotFoundError,
    ProductSearchHit,
    PurchaseListItem,
    ReplenishmentRecommendation,
)
from app.services import catalog_service

app = FastAPI(title="SupplyMate", version="0.2.0")


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


@app.get("/replenishment/purchase-list", response_model=list[PurchaseListItem])
async def purchase_list(limit: int = Query(default=25, ge=1, le=100)) -> list[PurchaseListItem]:
    recs = catalog_service.list_purchase_recommendations(limit=limit)
    return catalog_service.purchase_list_items(recs)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await run_supplymate(request.message)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
