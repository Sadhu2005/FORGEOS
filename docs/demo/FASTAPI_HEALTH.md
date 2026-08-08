# Demo — FastAPI `/health` (Phase 10)

Backend-only managed app: FastAPI + pytest + Compose. No Next.js, Postgres, or Redis.

## Prerequisites

```powershell
pip install -e ".[dev]"
```

Docker Desktop optional (needed only for real `compose_up`).

## Path A — Scaffold + mock plan/run (CI-friendly)

Run these **one command at a time** (PowerShell treats `<>` as operators — do not paste placeholders literally).

```powershell
forgeos init health-demo --scaffold
cd projects\health-demo\backend
pip install -r requirements.txt
pytest -q
cd ..\..\..
```

```powershell
forgeos plan health-demo --goal "Create a Python FastAPI project with a /health endpoint and tests" --template fastapi-health --force
forgeos tasks list health-demo
forgeos run health-demo --goal "Create a Python FastAPI project with a /health endpoint and tests" --steps 3 --llm mock
forgeos safety pending health-demo
```

Copy the real id from `pending` (example `appr-e861e4eba9c8`), then:

```powershell
forgeos safety approve health-demo --id appr-e861e4eba9c8
forgeos run health-demo --steps 3 --llm mock
```

With scaffold present, the plan is the **short** graph: `be-003` → `ops-001` → `ops-002` → `qa-001` → `doc-001`.

`ops-002` uses `docker.compose_up` and **blocks for human approval**.

## Path B — Full multi-role graph (no scaffold)

```powershell
forgeos init health-full
forgeos plan health-full --goal "Create a Python FastAPI project with a /health endpoint and tests" --force
forgeos run health-full --goal "Create a Python FastAPI project with a /health endpoint and tests" --steps 4 --llm mock
```

Writes architecture + `backend/app/main.py` + tests, then runs pytest (`be-003`). Compose still requires approval at `ops-002`.

## Ollama (enhancement)

```powershell
forgeos plan health-demo --goal "Create a Python FastAPI project with a /health endpoint and tests" --llm ollama --force
```

MockLLM always falls back to the FastAPI seed template when JSON is empty; Ollama may refine tasks but roles/tools should still match the managed-app pattern.

## Dashboard

```powershell
forgeos dashboard
```

Open the project → Approvals to approve `compose_up`.

## Local API without Compose

```powershell
cd projects\health-demo\backend
uvicorn app.main:app --port 8000
```

Then open **http://127.0.0.1:8000/health** (not bare `/` — that only returns a pointer JSON). Or try **http://127.0.0.1:8000/docs**.
