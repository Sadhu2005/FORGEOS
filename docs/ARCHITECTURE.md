# FORGEOS System Architecture

**FORGEOS** is a local AI Engineering Operating System: one intelligence loop that plans, executes, observes, verifies, and replans — not a swarm of concurrent agents.

## Core principle

```text
YOU → Orchestrator → RolePolicy → Context → Local LLM → Tools → Observe/Verify → Replan
```

- **One active LLM invocation at a time.** Roles are temporary policies (prompt + allowed paths + tools + Definition of Done), not separate processes competing for RAM/VRAM.
- **Reality > LLM opinion.** A role may claim “done”; only evidence (tests, build, health checks, file presence) marks work complete.
- **Evidence-backed memory.** World state, task graph, decisions, and audit events live outside the chat transcript so context stays small and grounded.

## System overview

```text
                         HUMAN
                           │
                           ▼
                    ┌─────────────┐
                    │  INTERFACE  │  (CLI first; dashboard later)
                    └──────┬──────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   ORCHESTRATOR      │
                └──────────┬──────────┘
                           │
           ┌───────────────┼────────────────┐
           │               │                │
           ▼               ▼                ▼
      WORLD STATE       PLANNER         RESOURCE
      ENGINE            ENGINE           GOVERNOR
           │               │                │
           └───────────────┼────────────────┘
                           ▼
                    DECISION ENGINE
                           │
                           ▼
                    CONTEXT ENGINE
                           │
                           ▼
                     MODEL ROUTER
                           │
                           ▼
                       LOCAL LLM  (Ollama — one model loaded)
                           │
                           ▼
                     TOOL ENGINE
                           │
       ┌──────────┬────────┼────────┬──────────┐
       ▼          ▼        ▼        ▼          ▼
    Filesystem  Terminal   Git     Tests      Docker
                           │
                           ▼
                       OBSERVER → VERIFIER → MEMORY / REPLAN
```

## Core loop

```text
PLAN → ACT → OBSERVE → VERIFY → MEMORIZE → REPLAN
```

Until the goal is complete or blocked for human review:

1. Inspect world state and select the next READY task.
2. Activate the matching **role policy**.
3. Build a minimal context (goal, task, summary, relevant files, errors, allowed tools).
4. Invoke the local model once.
5. Execute validated tool calls.
6. Verify Definition of Done with evidence.
7. Store results; on failure, classify and replan — do not infinite-retry blindly.

## World state

Ground truth for a managed project (not conversation history). Example shape:

```yaml
project:
  name: ExampleApp
  phase: mvp
  status: active
repository:
  branch: feature/auth
  clean: false
  last_commit: abc123
architecture:
  frontend: Next.js
  backend: FastAPI
  database: PostgreSQL
tasks:
  completed: 12
  pending: 5
  blocked: 1
tests:
  total: 40
  passing: 38
  failing: 2
environment:
  docker: available
  node: "22"
  python: "3.12"
```

Persisted under the project’s `.forge/` directory (see [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md)).

## Role pipeline

Roles run **sequentially** in LLM time. The task graph may show parallel edges (e.g. UI/UX and Database after Architecture); the orchestrator still executes one role at a time.

```text
Human goal
  → CEO → Product Manager → Software Architect
  → UI/UX + Database (graph-parallel, LLM-serial)
  → Frontend + Backend (graph-parallel, LLM-serial)
  → QA → (fail: replan) → Documentation → DevOps → Reporter → Human
```

Full permissions and handoffs: [ROLES.md](ROLES.md). End-to-end flow: [WORKFLOW.md](WORKFLOW.md).

## Two repositories of concern

| Scope | What lives here |
|---|---|
| **FORGEOS engine** | Orchestrator, planner, tools, role policies, benchmarks — this repo |
| **Managed project** | App monorepo (`frontend/`, `backend/`, `database/`, `docker/`, `docs/`, `.forge/`) that FORGEOS creates and drives |

**Runnable today:** Phase 0 benchmark + Phase 1–2 CLI/tools + Phase 3 Ollama path (`forgeos run --llm ollama`, `forgeos llm …`). See [PHASE3.md](PHASE3.md).

## Related documents

- [PHASE1.md](PHASE1.md) — Phase 1 ship notes
- [ENGINE_LAYOUT.md](ENGINE_LAYOUT.md) — package paths
- [MODEL_ROUTING.md](MODEL_ROUTING.md) — which local model to use
- [PHASES.md](PHASES.md) — phase map and Phase 1 DoD
- [ROLES.md](ROLES.md) — role policies
- [schemas/](schemas/) — world state / task / decision / role schemas
- [GIT_AND_RELEASE.md](GIT_AND_RELEASE.md) — branches, tags, SemVer
- [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md) — monorepo shape
- [API_VERSIONING.md](API_VERSIONING.md) — `/api/v1` rules
- [DOCKER.md](DOCKER.md) — local Compose topology
- [WORKFLOW.md](WORKFLOW.md) — goal → report pipeline

## Philosophy

> FORGEOS does not trust the model. It trusts evidence.
