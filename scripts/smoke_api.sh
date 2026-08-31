#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${SUPPLYMATE_API_URL:-http://127.0.0.1:8000}"

echo "Smoke: GET /health"
curl -sf "${BASE_URL}/health" | grep -q '"status":"ok"'

echo "Smoke: GET /replenishment/slice?limit=3"
curl -sf "${BASE_URL}/replenishment/slice?limit=3" | grep -q '"purchase_list"'

echo "Smoke: GET /replenishment/purchase-list.csv?limit=5"
csv="$(curl -sf "${BASE_URL}/replenishment/purchase-list.csv?limit=5")"
echo "$csv" | grep -q "barcode"
test "$(echo "$csv" | wc -l)" -ge 2

echo "Smoke: GET /products/6033436/replenishment"
curl -sf "${BASE_URL}/products/6033436/replenishment" | grep -q '"recommended_quantity":172'

echo "All smoke checks passed."
