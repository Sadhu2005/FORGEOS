# Demo — Next.js frontend slice (Phase 12)

Backend-only FastAPI stays the default. Next.js is optional via `--with-frontend`.

## Prerequisites

```powershell
pip install -e ".[dev]"
# Docker Desktop for compose up (optional)
# Node.js only needed for local `npm run dev`
```

## Steps

```powershell
forgeos init next-demo --scaffold --with-frontend
cd projects\next-demo\backend
pip install -r requirements.txt
pytest -q
cd ..\..\..

docker compose -f projects\next-demo\docker\docker-compose.yml config --services
# expect: backend frontend
```

## Local frontend (without Docker)

```powershell
# terminal 1
cd projects\next-demo\backend
uvicorn app.main:app --reload --port 8000

# terminal 2
cd projects\next-demo\frontend
$env:BACKEND_URL="http://127.0.0.1:8000"
npm install
npm run dev
# http://127.0.0.1:3000 — shows /api/v1/ping JSON
```

## Planner template

```powershell
forgeos plan next-demo --goal "Next.js frontend with FastAPI /api/v1/ping" --template fastapi-next-health --force
forgeos tasks list next-demo
```
