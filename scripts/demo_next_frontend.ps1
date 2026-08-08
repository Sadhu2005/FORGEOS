# FORGEOS Phase 12 — Next.js frontend demo (PowerShell)

$ErrorActionPreference = "Stop"
$Name = if ($args[0]) { $args[0] } else { "next-demo" }

Write-Host "== init --scaffold --with-frontend =="
forgeos init $Name --scaffold --with-frontend

Write-Host "== backend pytest =="
Push-Location "projects\$Name\backend"
pip install -r requirements.txt | Out-Null
pytest -q
Pop-Location

Write-Host "== compose services =="
docker compose -f "projects\$Name\docker\docker-compose.yml" config --services

Write-Host @"

Optional (Docker):
  docker compose -f projects\$Name\docker\docker-compose.yml up -d --build
  # open http://127.0.0.1:3000

Optional (local Node):
  `$env:BACKEND_URL="http://127.0.0.1:8000"`
  cd projects\$Name\frontend; npm install; npm run dev

Docs: docs/demo/NEXT_FRONTEND.md
"@
