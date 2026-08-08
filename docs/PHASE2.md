# Phase 2 — What shipped

Tag: `v0.3.0`  
Branch (during development): `feature/phase2-tool-engine`

## Shipped

- Shared `ToolResult` and `ToolRegistry` dispatch (`forgeos/tools/base.py`, `registry.py`)
- Filesystem expansions: `edit`, `search`, `tree`, `delete` (allowlisted; path escape denied)
- `terminal.execute` with project cwd sandbox, timeout, and dangerous-command deny list
- Git tools: `status`, `diff`, `branch`, `commit` (auto `git init` on first use); refuse force-push and `reset --hard`
- `testing.run` (pytest inside project)
- `docker.compose_config` only (no compose up / deploy)
- Executor dispatches via registry with role allowlist checks
- CLI: `forgeos tools list`, `forgeos tools exec`, `forgeos run --tool-demo`
- Role YAML updates for Phase 2 tool ids
- Schema: [schemas/tool_action.schema.yaml](schemas/tool_action.schema.yaml)
- Pytest coverage for registry, filesystem Phase 2, terminal, git, testing, docker, tools CLI

## Deferred

| Capability | Phase |
|---|---|
| Ollama client + model router | **3 (shipped in `v0.4.0` — see [PHASE3.md](PHASE3.md))** |
| Real hierarchical planner / replan | **4 (shipped in `v0.5.0`)** |
| Rich verification / failure taxonomy | 5 |
| SQLite memory | 6 |
| Approval gates / audit / git checkpoint; `docker compose up` / CRITICAL UI | 7 |
| Managed FastAPI `/health` demo (backend + compose) | **Shipped in Phase 10** — [PHASE10.md](PHASE10.md) |
| Managed Next.js generation as product demo | stretch / later |

## Demo

```powershell
pip install -e ".[dev]"
forgeos init demo
forgeos tools list
forgeos tools exec demo --role ceo --tool filesystem.tree --arg max_depth=2
forgeos run demo --tool-demo
forgeos run demo --goal "write hello report"
forgeos status demo
```
