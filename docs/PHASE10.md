# Phase 10 — Managed App Demo (v1.1.0)

## Shipped

- `forgeos init <name> --scaffold` writes a backend-only FastAPI `/health` tree (pytest, Docker Compose, docs stubs)
- Multi-role planner template `fastapi-health` (goal keyword detect or `--template`)
- Short verify+compose graph when `backend/app/main.py` already exists
- Real `docker.compose_up` (`up -d`); optional `dry_run=true` on the action
- Verifier checks: `pytest_pass`, `http_get:/path`
- `testing.run` supports `cwd` / `path` for backend tests
- Demo docs + PowerShell script; dashboard scaffold hint on empty projects

## Deferred

- Next.js frontend / full monorepo UI
- PostgreSQL / Redis for the health demo
- Replacing MockLLM as the default CLI backend (**Ollama plan path hardened in Phase 11** — see [PHASE11.md](PHASE11.md))
- Full CEO→…→Reporter autonomous pipeline without templates
- Cloud / production deploy

## Demo

See [docs/demo/FASTAPI_HEALTH.md](demo/FASTAPI_HEALTH.md) and `scripts/demo_fastapi_health.ps1`.

Canonical goal:

```text
Create a Python FastAPI project with a /health endpoint and tests
```
