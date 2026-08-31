param(
    [string]$BaseUrl = $(if ($env:SUPPLYMATE_API_URL) { $env:SUPPLYMATE_API_URL } else { "http://127.0.0.1:8000" })
)

$ErrorActionPreference = "Stop"

Write-Host "Smoke: GET /health"
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
if ($health.status -ne "ok") { throw "health check failed" }

Write-Host "Smoke: GET /replenishment/slice?limit=3"
$slice = Invoke-RestMethod -Uri "$BaseUrl/replenishment/slice?limit=3" -Method Get
if (-not $slice.purchase_list) { throw "slice missing purchase_list" }

Write-Host "Smoke: GET /replenishment/purchase-list.csv?limit=5"
$csv = Invoke-WebRequest -Uri "$BaseUrl/replenishment/purchase-list.csv?limit=5" -UseBasicParsing
if ($csv.Content -notmatch "barcode") { throw "csv missing header" }

Write-Host "Smoke: GET /products/6033436/replenishment"
$rec = Invoke-RestMethod -Uri "$BaseUrl/products/6033436/replenishment" -Method Get
if ($rec.recommended_quantity -ne 172) { throw "expected qty 172" }

Write-Host "All smoke checks passed."
