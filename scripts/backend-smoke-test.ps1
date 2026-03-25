$ErrorActionPreference = "Stop"

$baseUrl = if ($env:BASE_URL) { $env:BASE_URL.TrimEnd("/") } else { "http://127.0.0.1:8000" }
$apiBase = "$baseUrl/api/v1"

Write-Host "Running backend smoke test against $apiBase"

$health = Invoke-RestMethod -Method Get -Uri "$apiBase/health"
Write-Host "Health:" ($health | ConvertTo-Json -Compress)

$liveness = Invoke-RestMethod -Method Get -Uri "$apiBase/health/liveness"
Write-Host "Liveness:" ($liveness | ConvertTo-Json -Compress)

$db = Invoke-RestMethod -Method Get -Uri "$apiBase/health/db"
Write-Host "Database:" ($db | ConvertTo-Json -Compress)

$readiness = Invoke-RestMethod -Method Get -Uri "$apiBase/health/readiness"
Write-Host "Readiness:" ($readiness | ConvertTo-Json -Compress)

Write-Host "Smoke test completed."
