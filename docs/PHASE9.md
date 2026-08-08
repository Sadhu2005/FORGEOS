# Phase 9 — What shipped

Tag: `v1.0.0`  
Branch (during development): `feature/phase9-dashboard`

## Shipped

- Local stdlib HTTP dashboard under `forgeos/dashboard/`
- Project list (brand-first home), overview, tasks, approvals, audit, memory
- Interactive approve/reject (unblocks BLOCKED tasks + audit)
- Health / debt refresh and checkpoint create from the UI
- CLI: `forgeos dashboard` (default `http://127.0.0.1:18080/`; falls back if the port is blocked)
- Schema notes: [schemas/dashboard.schema.yaml](schemas/dashboard.schema.yaml)

## Deferred

| Capability | Later |
|---|---|
| Auth / multi-user | later |
| Public bind by default | never (opt-in `--allow-remote` only) |
| Streaming LLM console | later |
| Managed-app Next.js frontend | separate from engine |

## Demo

```powershell
pip install -e ".[dev]"
forgeos init demo
forgeos dashboard
# open http://127.0.0.1:18080/
```
