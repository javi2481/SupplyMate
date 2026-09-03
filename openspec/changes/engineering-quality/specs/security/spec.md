# Security spec (OWASP-minimal)

## Input validation (A03)

- `ChatRequest.message` MUST have `max_length=2000`
- Scope query param values MUST be truncated or rejected when exceeding 200 characters per value
- Scope lists MUST respect existing dimension limits (categories ≤ 5, etc.)

## Error handling (A05)

- When `SUPPLYMATE_ENV=production`, unhandled exceptions MUST return HTTP 500 with a generic message and MUST NOT expose stack traces in the response body

## Rate limiting (A07)

- `POST /chat` MUST return HTTP 429 when the same client exceeds `CHAT_RATE_LIMIT_PER_MIN` requests per minute
- `GET /health` MUST NOT be rate limited

## Headers

- All responses MUST include `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`

## Dependencies (A06)

- Project MUST document dependency audit procedure in `docs/operations/security-deps.md`
- CI MAY run `pip-audit` as non-blocking advisory
