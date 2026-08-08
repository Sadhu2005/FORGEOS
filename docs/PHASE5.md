# Phase 5 — What shipped

Tag: `v0.6.0`  
Branch (during development): `feature/phase5-verification`

## Shipped

- Expanded verifier: `exists`, `non_empty`, `contains:<text>`, `exit_code:N`
- `EvidenceBundle` written under `.forge/reports/evidence-*.yaml`
- `Observer.observe_exec` for tool/exec outcomes
- Rule-based `FailureClassifier` (syntax, dependency, logic, env, permission, timeout, unknown)
- Orchestrator classifies failures; replan stamps `[class]` into fix artifacts and reports
- CLI: `forgeos classify`, `forgeos verify <project> --task <id>`
- Schemas: [schemas/verify_result.schema.yaml](schemas/verify_result.schema.yaml), [schemas/failure.schema.yaml](schemas/failure.schema.yaml)

## Deferred

| Capability | Phase |
|---|---|
| SQLite memory / decision store | 6 |
| Approval gates / audit / git checkpoint | 7 |
| LLM-based failure diagnosis | later |
| Full QA role autonomy | later |
| Dashboard | 9 |

## Demo

```powershell
pip install -e ".[dev]"
forgeos classify --error "ModuleNotFoundError: No module named x"
forgeos init demo
forgeos plan demo --goal "ship phase5"
forgeos run demo --steps 1
forgeos verify demo --task task-001
```
