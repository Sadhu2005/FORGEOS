# Demo — Postgres Compose profile (Phase 11b)

Backend-only FastAPI stays the default. Postgres is optional via Compose profile `db`.

## Prerequisites

```powershell
pip install -e ".[dev]"
# Docker Desktop for compose --profile db
```

## Steps

```powershell
forgeos init pg-demo --scaffold --with-db
cd projects\pg-demo\backend
pip install -r requirements.txt
pytest -q
cd ..\..\..

# Backend only (no Postgres):
docker compose -f projects\pg-demo\docker\docker-compose.yml config

# With Postgres:
copy projects\pg-demo\.env.example projects\pg-demo\.env
docker compose -f projects\pg-demo\docker\docker-compose.yml --profile db up -d --build
```

## Health

Without `DATABASE_URL`: `{"status":"ok","database":"skipped"}`  
With DB up and URL set: `database` becomes `ok`.

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
```
