# FORGEOS Phases

| Phase | Branch | Tag (when exit met) | Exit criteria |
|---|---|---|---|
| 0 Benchmark | (merged to main) | `v0.1.0` | Ollama + bench harness + report |
| 0.5 Preflight | `feature/phase0-5-preflight` | `v0.1.1` | Schemas, role YAMLs, engine layout docs, package skeleton |
| 1 Core engine | `feature/phase1-core-engine` | `v0.2.0` | **Shipped** — see [PHASE1.md](PHASE1.md) and DoD below |
| 2 Tool engine | `feature/phase2-tool-engine` | `v0.3.0` | **Shipped** — see [PHASE2.md](PHASE2.md) |
| 3 LLM engine | `feature/phase3-llm-engine` | `v0.4.0` | **Shipped** — see [PHASE3.md](PHASE3.md) |
| 4 Planning | `feature/phase4-planning` | `v0.5.0` | **Shipped** — see [PHASE4.md](PHASE4.md) |
| 5 Verification | `feature/phase5-verification` | `v0.6.0` | **Shipped** — see [PHASE5.md](PHASE5.md) |
| 6 Memory | `feature/phase6-memory` | `v0.7.0` | **Shipped** — see [PHASE6.md](PHASE6.md) |
| 7 Safety | `feature/phase7-safety` | `v0.8.0` | **Shipped** — see [PHASE7.md](PHASE7.md) |
| 8 Eng. intelligence | `feature/phase8-engineering-intelligence` | `v0.9.0` | **Shipped** — see [PHASE8.md](PHASE8.md) |
| 9 Dashboard | `feature/phase9-dashboard` | `v1.0.0` | **Shipped** — see [PHASE9.md](PHASE9.md) |
| 10 Managed app | `feature/phase10-managed-app` | `v1.1.0` | **Shipped** — see [PHASE10.md](PHASE10.md) |
| 10.1 Patch | `hotfix/v1.1.1-windows-demo-fixes` | `v1.1.1` | **Shipped** — Windows demo/dashboard fixes |
| 11 Ollama + API | `feature/phase11-ollama-managed-backend` | `v1.2.0` | **Shipped** — see [PHASE11.md](PHASE11.md) |
| 11b Postgres profile | `feature/phase11b-postgres-compose` | `v1.3.0` | **Shipped** — see [PHASE11B.md](PHASE11B.md) |

`release/0.1.0` stays pinned at the `v0.1.0` freeze. Patch `v0.1.1` lives on `main` only (no new release branch). Phase 1 ships as `v0.2.0` with freeze branch `release/0.2.0`. Phase 2 ships as `v0.3.0` with freeze branch `release/0.3.0`. Phase 3 ships as `v0.4.0` with freeze branch `release/0.4.0`. Phase 4 ships as `v0.5.0` with freeze branch `release/0.5.0`. Phase 5 ships as `v0.6.0` with freeze branch `release/0.6.0`. Phase 6 ships as `v0.7.0` with freeze branch `release/0.7.0`. Phase 7 ships as `v0.8.0` with freeze branch `release/0.8.0`. Phase 8 ships as `v0.9.0` with freeze branch `release/0.9.0`. Phase 9 ships as `v1.0.0` with freeze branch `release/1.0.0`. Phase 10 ships as `v1.1.0` with freeze branch `release/1.1.0`. Patch `v1.1.1` freezes as `release/1.1.1`. Phase 11 ships as `v1.2.0` with freeze branch `release/1.2.0`. Phase 11b ships as `v1.3.0` with freeze branch `release/1.3.0`.

## Phase 1 — V1 CLI Definition of Done

Phase 1 is complete when all of the following are true:

1. **Package runnable:** `python -m forgeos` (or documented CLI entry) starts without import errors.
2. **World state:** Can create/load a project under `projects/<name>/` with `.forge/state.yaml` matching [schemas/world_state.schema.yaml](schemas/world_state.schema.yaml).
3. **Task graph (minimal):** Can represent tasks with statuses from [schemas/task.schema.yaml](schemas/task.schema.yaml) and pick a READY task.
4. **Role activation:** Loads a role from `roles/*.yaml` and applies path/tool allowlists in the orchestrator stub.
5. **Loop stub:** One PLAN → ACT → OBSERVE → VERIFY cycle runs against a trivial goal (e.g. create a file or write a short report) with evidence logged under `.forge/reports/`.
6. **No multi-agent concurrency:** Exactly one LLM call in flight (may be mocked in unit tests).
7. **Tests:** At least unit tests for world-state load/save and role loader.
8. **Docs:** CHANGELOG updated; this file’s Phase 1 row can be marked shipped when tagging `v0.2.0`.

Demo goal (stretch inside Phase 1 or early Phase 2; **shipped in Phase 10**):  
`forge "Create a Python FastAPI project with a /health endpoint and tests"` — see [PHASE10.md](PHASE10.md) and [demo/FASTAPI_HEALTH.md](demo/FASTAPI_HEALTH.md). Full autonomy was **not** required for Phase 1 exit; the stub loop + schemas were.

## Human gate

Merges to `main` and version tags follow [GIT_AND_RELEASE.md](GIT_AND_RELEASE.md).
