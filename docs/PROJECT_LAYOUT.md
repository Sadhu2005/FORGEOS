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
FORGEOS/                          # this repository (engine)
├── docs/                         # engine architecture pack + schemas
├── roles/                        # machine-readable role policies (YAML)
├── forgeos/                      # Python package (orchestrator starts Phase 1)
├── benchmarks/                   # Phase 0, etc.
├── projects/                     # default sandbox root (apps live here)
│   └── <managed-app>/            # standard tree above — NOT the engine
└── pyproject.toml
```

| Tree | Who owns it | Phase |
|---|---|---|
| `forgeos/`, `docs/`, `roles/`, `benchmarks/` | Engine | Phase 0.5+ |
| `projects/<app>/frontend|backend|…` | Managed app (roles write here) | When a goal creates an app |

Managed sandboxes may also live at a configurable absolute path. The engine never treats its own `docs/` pack as an application monorepo. Do **not** scaffold Next.js/FastAPI under the engine root; create those only inside `projects/<app>/`.

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
