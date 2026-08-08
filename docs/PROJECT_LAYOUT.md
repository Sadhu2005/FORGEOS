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
| `projects/<app>/frontend|backend|…` | Managed app (roles write here) | When a goal creates an app; **Phase 10:** `forgeos init <name> --scaffold` writes backend-only FastAPI `/health` + `docker/` + docs stubs |

Managed sandboxes may also live at a configurable absolute path. The engine never treats its own `docs/` pack as an application monorepo. Do **not** scaffold Next.js/FastAPI under the engine root; create those only inside `projects/<app>/` (use `init --scaffold` for the Phase 10 health demo).

## Defaults

- **Frontend:** Next.js (optional; not required for Phase 10 health demo)  
- **Backend:** FastAPI (`/health` in Phase 10 scaffold; `/api/v1` for fuller apps)  
- **Database:** PostgreSQL (+ Redis when Architect requires caching/sessions) — **not** required for Phase 10 `/health`  
- **Local runtime:** Docker Compose — see [DOCKER.md](DOCKER.md)

## `.forge/` runtime

| Item | Purpose |
|---|---|
| `state.yaml` | World state snapshot |
| `tasks.yaml` | Task graph (planner dual-writes SQLite memory) |
| `reports/` | QA and task reports + evidence YAML |
| `memory.sqlite` | Phase 6+ decisions/events mirror |
| `approvals/` | Phase 7 pending/approved tickets |
| `audit.jsonl` | Phase 7 safety audit |

Application code must not depend on `.forge/` at runtime; it is operator/engine metadata. Scaffolded apps still sync memory on `plan` / `run` like any other project.
