# Demo REST queries for SupplyMate (PowerShell)
$Base = if ($env:SUPPLYMATE_API_URL) { $env:SUPPLYMATE_API_URL } else { "http://127.0.0.1:8000" }

Write-Host "=== health ==="
Invoke-RestMethod "$Base/health"

Write-Host "`n=== search ==="
Invoke-RestMethod "$Base/products/search?q=47%20street" | ConvertTo-Json

Write-Host "`n=== product master ==="
Invoke-RestMethod "$Base/products/8141600" | ConvertTo-Json

Write-Host "`n=== replenishment (deterministic, no LLM) ==="
Invoke-RestMethod "$Base/products/6033436/replenishment" | ConvertTo-Json -Depth 5

Write-Host "`n=== chat (requires GROQ_API_KEY) ==="
$body = @{ message = "¿Cuánto debería pedir de 6033436?" } | ConvertTo-Json
try {
    Invoke-RestMethod -Method Post -Uri "$Base/chat" -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Chat skipped or failed: $_"
}
