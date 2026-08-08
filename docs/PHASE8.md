# Phase 8 — What shipped

Tag: `v0.9.0`  
Branch (during development): `feature/phase8-engineering-intelligence`

## Shipped

- `forgeos.intelligence.health`: probe tests/env/compose → `.forge/health.yaml` + `state.tests` / `state.environment`
- `forgeos.intelligence.debt`: TODO/FIXME/HACK + blocked tasks + pending approvals → `.forge/debt.yaml`
- `forgeos.intelligence.research`: local docs/reports search (no network)
- Tools: `research`, `world_state.read` (Architect role ids resolve)
- ContextManager injects `## Health` / `## Debt` when artifacts exist
- Orchestrator `refresh_light` (debt scan only) after plan/run memory sync
- CLI: `forgeos intelligence health|debt|research`
- Schema: [schemas/intelligence.schema.yaml](schemas/intelligence.schema.yaml)

## Deferred

| Capability | Phase |
|---|---|
| Dashboard UI over engine | **9 (shipped in `v1.0.0` — see [PHASE9.md](PHASE9.md))** |
| External web research / SaaS debt tools | later |
| Auto pytest on every orchestrator cycle | later |

## Demo

```powershell
pip install -e ".[dev]"
forgeos init demo
forgeos intelligence health demo
forgeos intelligence debt demo
forgeos intelligence research demo --query "architecture"
```
