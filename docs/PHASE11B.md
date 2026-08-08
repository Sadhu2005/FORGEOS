# Phase 11b — Optional Postgres Compose (v1.3.0)

## Shipped

- Scaffold `docker-compose.yml` includes **Postgres** under Compose profile **`db`**
- Default `up` remains backend-only (no profile)
- `forgeos init <name> --scaffold --with-db` (or `--with-db` alone) writes `.env.example` + DB docs
- `/health` returns `database: skipped|ok|error` via optional `DATABASE_URL` + `psycopg`
- Demo: [docs/demo/POSTGRES_PROFILE.md](demo/POSTGRES_PROFILE.md), `scripts/demo_postgres_profile.ps1`

## Deferred

- Redis
- ORM / migrations / Alembic
- Next.js frontend (**shipped in Phase 12** — see [PHASE12.md](PHASE12.md))
- Cloud deploy
- Auto-wiring backend container `depends_on` + internal hostname (docs use localhost for host uvicorn)

## Usage

```powershell
forgeos init app --scaffold --with-db
docker compose -f projects/app/docker/docker-compose.yml --profile db up -d --build
```
