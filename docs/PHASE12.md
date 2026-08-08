# Phase 12 — Frontend Slice (v1.4.0)

## Shipped

- Optional Next.js App Router frontend via `forgeos init --scaffold --with-frontend`
- Compose `frontend` service on `:3000` with `BACKEND_URL=http://backend:8000`
- One server-side fetch to backend `GET /api/v1/ping`
- Planner template **`fastapi-next-health`** (full + short)
- Demo: [docs/demo/NEXT_FRONTEND.md](demo/NEXT_FRONTEND.md), `scripts/demo_next_frontend.ps1`

## Deferred

- Auth / sessions
- Redis
- Design system / UI kit / UI-UX role outputs under `design/`
- ORM / migrations
- Production Next.js `build`+`start` image (scaffold uses `next dev` in container for simplicity)
- Cloud deploy

## Usage

```powershell
forgeos init app --scaffold --with-frontend
docker compose -f projects/app/docker/docker-compose.yml up -d --build
# http://127.0.0.1:3000
```

```powershell
forgeos plan app --goal "Next.js frontend with FastAPI ping" --template fastapi-next-health
```
