# Managed Project Layout

Every project FORGEOS creates or manages uses this **monorepo** shape. The Software Architect may refine internals; they must not invent a random top-level tree without a decision record.

## Standard tree

```text
project/
├── frontend/              # Next.js (default unless Architect documents otherwise)
├── backend/               # FastAPI, public API under /api/v1
├── database/
│   ├── schema.sql
│   ├── migrations/
│   │   ├── 001_init.sql
│   │   └── ...
│   └── database.md
├── design/                # UI/UX role outputs
│   ├── design-system.md
│   ├── pages.md
│   ├── components.md
│   └── user-flows.md
├── docker/
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   └── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md
│   └── REQUIREMENTS.md    # Product Manager (optional path)
├── .forge/                # FORGEOS runtime (world state, reports, audit)
│   ├── state.yaml
│   └── reports/
├── README.md
└── CHANGELOG.md
```

## Ownership by path

| Path | Primary role |
|---|---|
| `frontend/` | Frontend |
| `backend/` | Backend |
| `database/` | Database |
| `design/` | UI/UX |
| `docker/`, CI configs, `.env.example` | DevOps |
| `docs/`, `CHANGELOG.md`, root `README.md` | Documentation (Architect owns initial `docs/ARCHITECTURE.md`) |
| `.forge/` | FORGEOS engine (all roles may read; orchestrator writes state) |

## FORGEOS engine vs managed projects

```text
FORGEOS/                          # this repository
├── docs/                         # engine architecture pack
├── benchmarks/                   # Phase 0, etc.
├── core/  llm/  tools/  ...      # later phases
└── projects/                     # optional default sandbox root
    └── <managed-app>/            # standard tree above
```

Managed sandboxes may also live at a configurable absolute path. The engine never treats its own `docs/` pack as an application monorepo.

## Defaults

- **Frontend:** Next.js  
- **Backend:** FastAPI mounted at `/api/v1`  
- **Database:** PostgreSQL (+ Redis when Architect requires caching/sessions)  
- **Local runtime:** Docker Compose — see [DOCKER.md](DOCKER.md)

## `.forge/` runtime

| Item | Purpose |
|---|---|
| `state.yaml` | World state snapshot |
| `reports/` | QA and task reports |
| (later) task graph DB / audit log | Replayability and evidence |

Application code must not depend on `.forge/` at runtime; it is operator/engine metadata.
