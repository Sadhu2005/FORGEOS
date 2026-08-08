# Phase 1 — What shipped

Tag: `v0.2.0`  
Branch (during development): `feature/phase1-core-engine`

## Shipped

- Runnable CLI: `forgeos init|run|status` and `python -m forgeos`
- World state create/load/save under `projects/<name>/.forge/state.yaml`
- Minimal task graph with READY selection
- Role YAML loader with required-field validation
- One PLAN → ACT → OBSERVE → VERIFY cycle using `MockLLM`
- Minimal `filesystem` tool with role path allowlists
- Task reports under `.forge/reports/`
- Pytest coverage for core paths

## Deferred

| Capability | Phase |
|---|---|
| Full terminal / git / docker tools | **2 (shipped in `v0.3.0` — see [PHASE2.md](PHASE2.md))** |
| Ollama client + model router | 3 |
| Real hierarchical planner / replan | 4 |
| Rich verification / failure taxonomy | 5 |
| SQLite memory | 6 |
| Approval gates / audit / git checkpoint | 7 |

## Demo

```powershell
pip install -e ".[dev]"
forgeos init demo
forgeos run demo --goal "write hello report"
forgeos status demo
```
