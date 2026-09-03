"""Rate limit POST /chat and POST /replenishment/analyze by client IP."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import effective_analyze_rate_limit, effective_chat_rate_limit
from app.middleware.rate_limit import allow_request


class ChatRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path.rstrip("/")
        if request.method == "POST":
            if path == "/chat":
                client = request.client.host if request.client else "unknown"
                if not allow_request(f"chat:{client}", effective_chat_rate_limit()):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                    )
            elif path == "/replenishment/analyze":
                client = request.client.host if request.client else "unknown"
                if not allow_request(f"analyze:{client}", effective_analyze_rate_limit()):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                    )
        return await call_next(request)
