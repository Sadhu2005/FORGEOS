# FORGEOS Phase 10 — FastAPI health demo (PowerShell)

$ErrorActionPreference = "Stop"
$Name = if ($args[0]) { $args[0] } else { "health-demo" }
$Goal = "Create a Python FastAPI project with a /health endpoint and tests"

Write-Host "== init --scaffold =="
forgeos init $Name --scaffold

Write-Host "== backend pytest =="
Push-Location "projects\$Name\backend"
pip install -r requirements.txt | Out-Null
pytest -q
Pop-Location

Write-Host "== plan (fastapi-health) =="
forgeos plan $Name --goal $Goal --template fastapi-health --force
forgeos tasks list $Name

Write-Host "== run through verify (mock; may stop at compose approval) =="
forgeos run $Name --goal $Goal --steps 3 --llm mock

Write-Host "== pending approvals (compose_up) =="
forgeos safety pending $Name

Write-Host @"

Next (PowerShell — use the real id from pending, do not type angle brackets):
  forgeos safety approve $Name --id appr-xxxxxxxx
  forgeos run $Name --goal "$Goal" --steps 3 --llm mock
  # If Docker is available, compose_up starts the backend; then:
  # http://127.0.0.1:8000/health

Docs: docs/demo/FASTAPI_HEALTH.md
"@
