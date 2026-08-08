# Phase 7 — What shipped

Tag: `v0.8.0`  
Branch (during development): `feature/phase7-safety`

## Shipped

- `forgeos.safety.permissions`: critical gate for task risk, `filesystem.delete` / `docker.compose_up`, and `git.commit` on protected branches / without `may_commit_feature_branch`
- File-based approvals under `.forge/approvals/*.yaml`; orchestrator BLOCKs until `forgeos safety approve`
- Append-only `.forge/audit.jsonl` + memory event dual-write (`permission` / `approval` / `checkpoint`)
- Git checkpoints: `.forge/checkpoints.yaml` + tag `forgeos-ckpt-<utc>` when HEAD exists
- Tools: `git.checkpoint`, `docker.compose_up` (approval-gated)
- CLI: `forgeos safety pending|approve|reject|audit`, `forgeos checkpoint create|list`
- Schema: [schemas/approval.schema.yaml](schemas/approval.schema.yaml)

## Deferred

| Capability | Phase |
|---|---|
| Interactive approval TUI / dashboard | **9 (shipped in `v1.0.0` — see [PHASE9.md](PHASE9.md))** |
| Eng-intelligence health/debt/research hooks | **8 (shipped in `v0.9.0` — see [PHASE8.md](PHASE8.md))** |
| Force-push / reset --hard / cloud prod deploy | never (policy) |
| SQLite approval/audit tables | later |

## Demo

```powershell
pip install -e ".[dev]"
forgeos init demo
# Seed or run a critical tool task; then:
forgeos safety pending demo
forgeos safety approve demo --id appr-...
forgeos run demo --steps 1
forgeos checkpoint create demo --message "pre-change"
forgeos checkpoint list demo
forgeos safety audit demo
```
