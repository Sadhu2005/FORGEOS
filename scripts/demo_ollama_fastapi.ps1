# FORGEOS Phase 11 — Ollama FastAPI plan demo (PowerShell)

$ErrorActionPreference = "Stop"
$Name = if ($args[0]) { $args[0] } else { "ollama-demo" }
$Goal = "Create a Python FastAPI project with a /health endpoint and tests"

Write-Host "== llm status =="
forgeos llm status

Write-Host "== init --scaffold =="
forgeos init $Name --scaffold

Write-Host "== backend pytest =="
Push-Location "projects\$Name\backend"
pip install -r requirements.txt | Out-Null
pytest -q
Pop-Location

Write-Host "== plan with Ollama (bounded timeout) =="
$env:FORGEOS_OLLAMA_TIMEOUT = "120"
forgeos plan $Name --goal $Goal --template fastapi-health --llm ollama --force
forgeos tasks list $Name

Write-Host "== run short path with mock =="
forgeos run $Name --goal $Goal --steps 2 --llm mock

Write-Host @"

API:
  cd projects\$Name\backend
  uvicorn app.main:app --port 8000
  # /health and /api/v1/ping

Docs: docs/demo/OLLAMA_FASTAPI.md
"@
