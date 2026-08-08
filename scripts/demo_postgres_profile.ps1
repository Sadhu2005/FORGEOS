# FORGEOS Phase 11b — Postgres profile demo (PowerShell)

$ErrorActionPreference = "Stop"
$Name = if ($args[0]) { $args[0] } else { "pg-demo" }

Write-Host "== init --scaffold --with-db =="
forgeos init $Name --scaffold --with-db

Write-Host "== backend pytest =="
Push-Location "projects\$Name\backend"
pip install -r requirements.txt | Out-Null
pytest -q
Pop-Location

Write-Host "== compose config =="
docker compose -f "projects\$Name\docker\docker-compose.yml" config | Select-Object -First 20

Write-Host @"

Optional (Docker required):
  Copy-Item projects\$Name\.env.example projects\$Name\.env
  docker compose -f projects\$Name\docker\docker-compose.yml --profile db up -d --build
  # curl http://127.0.0.1:8000/health

Docs: docs/demo/POSTGRES_PROFILE.md
"@
