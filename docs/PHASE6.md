# Phase 6 — What shipped

Tag: `v0.7.0`  
Branch (during development): `feature/phase6-memory`

## Shipped

- Per-project SQLite store at `projects/<name>/.forge/memory.sqlite` (stdlib `sqlite3`)
- Tables: `project_meta`, `tasks`, `decisions`, `events`
- `Repository.sync_from_yaml` dual-writes world state + task graph; YAML remains authoritative for planner load
- `Summarizer` short grounded summary; hooked into `ContextManager.build` as `## Memory`
- Orchestrator syncs after plan/run; records cycle/verify/replan/classify events; failure decisions (`retry`/`block`)
- CLI: `forgeos memory status|decisions|sync`
- Schema notes: [schemas/memory.schema.yaml](schemas/memory.schema.yaml)

## Deferred

| Capability | Phase |
|---|---|
| Replace YAML world state entirely | later |
| Vector / embedding memory | later |
| Cross-project global DB | later |
| Approval gates / audit / git checkpoint | 7 |
| Eng-intelligence health/debt hooks | 8 |
| Dashboard over memory | 9 |

## Demo

```powershell
pip install -e ".[dev]"
forgeos init demo
forgeos plan demo --goal "ship phase6"
forgeos run demo --steps 1
forgeos memory sync demo
forgeos memory status demo
forgeos memory decisions demo
```
