# Docker and Local Runtime

FORGEOS treats **Docker Compose as the default local runtime** for managed application services. The LLM runtime stays on the host.

**Scope before Phase 1:** The FORGEOS engine repo does **not** require its own `docker-compose.yml` for core development. Ollama and the orchestrator run on the **host**. Compose files belong under each managed project’s `docker/` tree when that project is created — not as a Phase 0.5 / Phase 1 engine prerequisite.

## Topology

```text
┌────────────── Host machine ──────────────┐
│  FORGEOS CLI / orchestrator              │
│  Ollama (one model loaded)               │
│         │                    │             │
│         │ tools              │ LLM API     │
│         ▼                    │             │
│  ┌──── docker compose ────┐  │             │
│  │  frontend (Next.js)    │  │             │
│  │  backend  (FastAPI)    │◄─┘             │
│  │  postgres              │                │
│  │  redis (when required) │                │
│  └────────────────────────┘                │
└────────────────────────────────────────────┘
```

- **Ollama runs on the host**, not inside Compose — so GPU/VRAM and “one model loaded” stay under FORGEOS resource governance.
- Containers run the **app stack** only. They do not load LLMs.

## Files (DevOps role)

Under each managed project:

```text
docker/
├── Dockerfile.frontend
├── Dockerfile.backend
└── docker-compose.yml
```

Root may also reference Compose via `docker compose -f docker/docker-compose.yml` (exact invocation is DevOps-owned).

## Phase 10 backend-only demo

`forgeos init <name> --scaffold` writes a **backend-only** Compose stack:

```text
docker/
├── Dockerfile.backend
└── docker-compose.yml   # service: backend + /health healthcheck
```

No frontend, Postgres, or Redis for the `/health` demo. `docker.compose_up` is CRITICAL and needs `forgeos safety approve` (or the dashboard Approvals page) before containers start. Action flag `dry_run: true` runs `up -d --dry-run` only.

See [demo/FASTAPI_HEALTH.md](demo/FASTAPI_HEALTH.md).

## Expected services

| Service | Role |
|---|---|
| `frontend` | Next.js UI; calls backend `/api/v1` |
| `backend` | FastAPI app |
| `postgres` | Primary database |
| `redis` | Cache/sessions when Architect requires it |

Object storage may be local MinIO or a stub until needed; Architect documents the choice.

## Health and validation

DevOps and QA should be able to:

- `docker compose config` — compose file valid  
- Healthchecks on backend (and DB readiness)  
- Local `up` / `down` without cloud credentials  

## Boundaries and safety

1. Dangerous host commands remain gated by FORGEOS permissions (CRITICAL → human).
2. Compose networks isolate app traffic; FORGEOS tools still validate paths and commands.
3. Secrets via `.env` / `.env.example`; never commit real secrets.
4. **Cloud deploy** (Vercel, Render, AWS, etc.) is out of scope until local Compose + health checks are reliable. Prod-like deploy always needs CRITICAL human approval.

## How FORGEOS uses Docker

| Actor | Action |
|---|---|
| DevOps role | Author/update Dockerfiles and Compose |
| QA role | `docker compose config`; optional smoke against running stack |
| Backend/Frontend roles | Develop against Compose services or documented local run |
| Orchestrator | Does not run models in containers |

## Relation to the engine repo

The FORGEOS repository itself may later add optional Compose for demos; Phase 0 benchmarks do not require Docker. Managed projects always get the `docker/` tree as part of the standard layout ([PROJECT_LAYOUT.md](PROJECT_LAYOUT.md)).
