from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse

from app.agent import run_analyze, run_supplymate
from app.core.config import MAX_SCOPE_VALUE_LENGTH
from app.middleware.chat_rate_limit import ChatRateLimitMiddleware
from app.middleware.safe_errors import SafeErrorMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.core.models import (
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
from app.services.scoping.scope_sanitize import sanitize_value, sanitize_values

APP_TITLE = "SupplyMate API"
APP_VERSION = "0.5.0"
APP_DESCRIPTION = """
API de **reposición inteligente** para operación comercial.

| Área | Qué hace |
|------|----------|
| Chat | Interpreta preguntas naturales y arma el recorte (`POST /chat`) |
| Reposición | Slice, dashboard, lista de compra y análisis |
| Catálogo | Búsqueda de productos y cálculo por SKU |

La UI de demo corre con `streamlit run ui/streamlit_app.py`.
""".strip()

OPENAPI_TAGS = [
    {"name": "system", "description": "Salud y descubrimiento del servicio"},
    {"name": "catalog", "description": "Productos del catálogo y reposición unitaria"},
    {"name": "replenishment", "description": "Recortes, dashboards, OC y análisis"},
    {"name": "chat", "description": "Asistente conversacional de reposición"},
]

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(ChatRateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SafeErrorMiddleware)

_ROOT_LINKS = {
    "docs": "/docs",
    "redoc": "/redoc",
    "health": "/health",
    "openapi": "/openapi.json",
    "chat": "POST /chat",
    "slice": "GET /replenishment/slice",
}

_PAGE_CSS = """
:root {
  --bg: #0b0f17;
  --panel: #12151c;
  --text: #e8eef7;
  --muted: rgba(232, 238, 247, 0.65);
  --accent: #1E88E5;
  --border: #2d3548;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  font-family: "Segoe UI", system-ui, sans-serif;
  background:
    radial-gradient(ellipse at top left, rgba(30, 136, 229, 0.18), transparent 45%),
    var(--bg);
  color: var(--text);
  display: grid;
  place-items: center;
  padding: 2rem;
}
main {
  width: min(40rem, 100%);
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.75rem 1.9rem;
}
h1 {
  margin: 0 0 0.35rem;
  font-size: 1.65rem;
  letter-spacing: -0.02em;
}
p { margin: 0 0 1.1rem; color: var(--muted); line-height: 1.45; }
ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.55rem; }
a.card {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  text-decoration: none;
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.7rem 0.85rem;
  background: rgba(255,255,255,0.02);
}
a.card:hover { border-color: var(--accent); }
a.card span { color: var(--muted); font-size: 0.9rem; }
a.card strong { color: var(--accent); font-weight: 600; }
table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
th, td { text-align: left; padding: 0.45rem 0.35rem; border-bottom: 1px solid var(--border); }
th { color: var(--muted); font-weight: 600; }
code { color: var(--accent); }
.meta { font-size: 0.85rem; color: var(--muted); margin-bottom: 1rem; }
.actions { display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 1rem; }
.actions a {
  color: var(--accent);
  text-decoration: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.4rem 0.7rem;
}
.actions a:hover { border-color: var(--accent); }
""".strip()


def _wants_html(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    if "text/html" not in accept:
        return False
    html_pos = accept.find("text/html")
    json_pos = accept.find("application/json")
    if json_pos != -1 and json_pos < html_pos:
        return False
    return True


def _root_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(APP_TITLE)}</title>
  <style>{_PAGE_CSS}</style>
</head>
<body>
  <main>
    <h1>{escape(APP_TITLE)}</h1>
    <p>Asesor de reposición. Esta es la raíz del servicio; usá los atajos de abajo.</p>
    <ul>
      <li><a class="card" href="/docs"><strong>Documentación interactiva</strong><span>/docs</span></a></li>
      <li><a class="card" href="/health"><strong>Estado del servicio</strong><span>/health</span></a></li>
      <li><a class="card" href="/openapi.json"><strong>Esquema OpenAPI</strong><span>/openapi.json</span></a></li>
    </ul>
  </main>
</body>
</html>
"""


def _openapi_html(schema: dict) -> str:
    info = schema.get("info") or {}
    paths = schema.get("paths") or {}
    rows: list[str] = []
    for path, methods in sorted(paths.items()):
        for method in sorted(methods):
            if method.startswith("x-"):
                continue
            summary = (methods[method] or {}).get("summary") or ""
            rows.append(
                "<tr>"
                f"<td><code>{escape(method.upper())}</code></td>"
                f"<td><code>{escape(path)}</code></td>"
                f"<td>{escape(str(summary))}</td>"
                "</tr>"
            )
    body_rows = "\n".join(rows) or "<tr><td colspan='3'>Sin rutas públicas listadas.</td></tr>"
    desc = escape(str(info.get("description") or "").split("\n")[0])
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(str(info.get("title") or APP_TITLE))} · OpenAPI</title>
  <style>{_PAGE_CSS}</style>
</head>
<body>
  <main>
    <h1>{escape(str(info.get("title") or APP_TITLE))}</h1>
    <p class="meta">OpenAPI {escape(str(schema.get("openapi") or "3.x"))}
 · v{escape(str(info.get("version") or APP_VERSION))}</p>
    <p>{desc or "Esquema machine-readable del servicio."}</p>
    <table>
      <thead><tr><th>Método</th><th>Ruta</th><th>Resumen</th></tr></thead>
      <tbody>
        {body_rows}
      </tbody>
    </table>
    <div class="actions">
      <a href="/docs">Abrir Swagger UI</a>
      <a href="/redoc">Abrir ReDoc</a>
      <a href="/openapi.json" download>Descargar JSON</a>
    </div>
  </main>
</body>
</html>
"""


def _build_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    app.openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    return app.openapi_schema


@app.get("/", include_in_schema=False)
async def root(request: Request) -> Response:
    if _wants_html(request):
        return HTMLResponse(_root_html())
    return JSONResponse(
        {
            "service": "SupplyMate",
            "version": APP_VERSION,
            "status": "ok",
            "message": "API de reposición. Usá /docs para explorar los endpoints.",
            "links": _ROOT_LINKS,
        }
    )


@app.get("/health", tags=["system"], summary="Estado del servicio")
async def health() -> dict[str, str]:
    return {
        "service": "SupplyMate",
        "version": APP_VERSION,
        "status": "ok",
        "message": "Servicio operativo y listo para recibir requests.",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/openapi.json", include_in_schema=False)
async def openapi_json(request: Request) -> Response:
    schema = _build_openapi()
    if _wants_html(request):
        return HTMLResponse(_openapi_html(schema))
    return JSONResponse(schema)


@app.get("/docs", include_in_schema=False)
async def swagger_docs() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{APP_TITLE} · Docs",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_docs() -> HTMLResponse:
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{APP_TITLE} · ReDoc",
    )


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


@app.get("/products/search", response_model=list[ProductSearchHit], tags=["catalog"], summary="Buscar productos")
async def search_products(q: str = Query(min_length=1)) -> list[ProductSearchHit]:
    return catalog_service.search_products(q)


@app.get("/products/{product_id}", response_model=ProductMaster, tags=["catalog"], summary="Obtener producto")
async def get_product(product_id: str) -> ProductMaster:
    try:
        return catalog_service.get_master(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/products/{product_id}/replenishment",
    response_model=ReplenishmentRecommendation,
    tags=["catalog"],
    summary="Reposición de un SKU",
)
async def get_replenishment(product_id: str) -> ReplenishmentRecommendation:
    try:
        return catalog_service.get_replenishment_recommendation(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/replenishment/slice",
    response_model=ReplenishmentSlice,
    tags=["replenishment"],
    summary="Slice de reposición del alcance",
)
async def replenishment_slice(
    scope: AnalyticalScope = Depends(_scope_dependency),
    limit: int = Query(default=25, ge=1, le=100),
) -> ReplenishmentSlice:
    return catalog_service.replenishment_slice(scope, limit=limit)


@app.get(
    "/replenishment/dashboard",
    response_model=InventoryDashboard,
    tags=["replenishment"],
    summary="Dashboard del alcance",
)
async def inventory_dashboard(
    scope: AnalyticalScope = Depends(_scope_dependency),
) -> InventoryDashboard:
    snap, _items = catalog_service.chat_dashboard(limit=1, scope=scope)
    return snap


@app.get(
    "/replenishment/purchase-list",
    response_model=list[PurchaseListItem],
    tags=["replenishment"],
    summary="Lista de compra",
)
async def purchase_list(
    scope: AnalyticalScope = Depends(_scope_dependency),
    limit: int = Query(default=25, ge=1, le=100),
) -> list[PurchaseListItem]:
    _snap, items = catalog_service.chat_dashboard(limit=limit, scope=scope)
    return items


@app.get("/replenishment/purchase-list.csv", tags=["replenishment"], summary="Exportar OC (CSV)")
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


@app.post(
    "/replenishment/analyze",
    response_model=AnalyzeResponse,
    tags=["replenishment"],
    summary="Análisis / lectura del recorte",
)
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


@app.post("/chat", response_model=ChatResponse, tags=["chat"], summary="Chat de reposición")
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
