# FORGEOS Phases

| Phase | Branch | Tag (when exit met) | Exit criteria |
|---|---|---|---|
| 0 Benchmark | (merged to main) | `v0.1.0` | Ollama + bench harness + report |
| 0.5 Preflight | `feature/phase0-5-preflight` | `v0.1.1` | Schemas, role YAMLs, engine layout docs, package skeleton |
| 1 Core engine | `feature/phase1-core-engine` | `v0.2.0` | **Shipped** — see [PHASE1.md](PHASE1.md) and DoD below |
| 2 Tool engine | `feature/phase2-tool-engine` | `v0.3.0` | Filesystem, terminal, git, test tools validated |
| 3 LLM engine | `feature/phase3-llm-engine` | `v0.4.0` | Ollama client, router, context builder |
| 4 Planning | `feature/phase4-planning` | `v0.5.0` | Task graph, next-task selection, replan |
| 5 Verification | `feature/phase5-verification` | `v0.6.0` | Evidence-based DoD checks, failure classify |
| 6 Memory | `feature/phase6-memory` | `v0.7.0` | SQLite project/task/decision store |
| 7 Safety | `feature/phase7-safety` | `v0.8.0` | Permissions, approval gates, audit, git checkpoint |
| 8 Eng. intelligence | `feature/phase8-engineering-intelligence` | `v0.9.0` | Health/debt/research hooks |
| 9 Dashboard | `feature/phase9-dashboard` | `v1.0.0` | UI over engine (after CLI solid) |

`release/0.1.0` stays pinned at the `v0.1.0` freeze. Patch `v0.1.1` lives on `main` only (no new release branch). Phase 1 ships as `v0.2.0` with freeze branch `release/0.2.0`.

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

Demo goal (stretch inside Phase 1 or early Phase 2):  
`forge "Create a Python FastAPI project with a /health endpoint and tests"` — full autonomy is **not** required for Phase 1 exit; the stub loop + schemas are.

## Human gate

Merges to `main` and version tags follow [GIT_AND_RELEASE.md](GIT_AND_RELEASE.md).
