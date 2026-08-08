# Phase 4 — What shipped

Tag: `v0.5.0`  
Branch (during development): `feature/phase4-planning`

## Shipped

- Expanded task graph: `deps_completed`, `promote_ready`, `attempts` / `last_error`
- `Scheduler` — promote PROPOSED→READY and pick next READY by priority
- `HierarchicalPlanner` with deterministic 2-task `.forge` template; LLM JSON parse best-effort + fallback
- `PlannerStub` kept as thin alias of `HierarchicalPlanner`
- `Replanner` with max attempts (default 3) → fix task or BLOCKED
- Orchestrator: `ensure_plan`, schedule-driven `run_once`, `run_steps`, execute via **task.role**
- CLI: `forgeos plan`, `forgeos tasks list`, `forgeos run --steps N`
- Schema: [schemas/plan.schema.yaml](schemas/plan.schema.yaml)
- Pytest coverage for scheduler, planner, replan, multi-step orchestrator, CLI

## Deferred

| Capability | Phase |
|---|---|
| Rich failure classification taxonomy | 5 |
| SQLite memory | 6 |
| Approval gates / audit / git checkpoint | 7 |
| Full 11-role autonomous product pipeline | later |
| Dashboard | 9 |

## Demo

```powershell
pip install -e ".[dev]"
forgeos init demo
forgeos plan demo --goal "ship phase4"
forgeos tasks list demo
forgeos run demo --steps 2 --goal "ship phase4"
forgeos status demo
```
