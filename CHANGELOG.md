# Changelog

All notable changes to FORGEOS are documented here.

## [1.1.1] — 2026-08-08

### Fixed

- Docker tool: UTF-8 decode of compose output on Windows (avoids cp1252 crash)
- QA role: allow `filesystem.write` for `.forge/reports/qa-*` reports
- Dashboard: default port `18080` + fallbacks (Windows Hyper-V reserves ~8571–9270)
- Scaffold: `backend/pytest.ini` so managed-app tests find `app`; root `/` JSON pointer
- Demo docs/script: PowerShell-safe approval instructions (no angle-bracket placeholders)

### Changed

- Package version `1.1.1`

## [1.1.0] — 2026-08-08

### Added

- Phase 10 managed-app demo: `forgeos init --scaffold` FastAPI `/health` tree
- Multi-role `fastapi-health` planner template (`--template` / goal detect)
- Verifier: `pytest_pass`, `http_get:/path`; `testing.run` `cwd`/`path`
- Real `docker.compose_up` (`up -d`) with optional action `dry_run`
- [docs/PHASE10.md](docs/PHASE10.md), [docs/demo/FASTAPI_HEALTH.md](docs/demo/FASTAPI_HEALTH.md), `scripts/demo_fastapi_health.ps1`

### Changed

- Package version `1.1.0`

## [1.0.0] — 2026-08-08

### Added

- Phase 9 local dashboard: stdlib HTTP UI over engine APIs
- Interactive approvals, health/debt refresh, checkpoints from the browser
- CLI: `forgeos dashboard` (loopback `127.0.0.1:8765`)
- [docs/PHASE9.md](docs/PHASE9.md); [docs/schemas/dashboard.schema.yaml](docs/schemas/dashboard.schema.yaml)

### Changed

- Package version `1.0.0`

## [0.9.0] — 2026-08-08

### Added

- Phase 8 engineering intelligence: health probe, debt scan, local research
- Tools: `research`, `world_state.read`
- Context `## Health` / `## Debt`; orchestrator light debt refresh
- CLI: `forgeos intelligence health|debt|research`
- [docs/PHASE8.md](docs/PHASE8.md); [docs/schemas/intelligence.schema.yaml](docs/schemas/intelligence.schema.yaml)

### Changed

- Package version `0.9.0`

## [0.8.0] — 2026-08-08

### Added

- Phase 7 safety: permissions gate, file-based approvals, audit JSONL, git checkpoints
- Tools: `git.checkpoint`, `docker.compose_up` (approval-gated)
- CLI: `forgeos safety pending|approve|reject|audit`, `forgeos checkpoint create|list`
- [docs/PHASE7.md](docs/PHASE7.md); [docs/schemas/approval.schema.yaml](docs/schemas/approval.schema.yaml)

### Changed

- Package version `0.8.0`

## [0.7.0] — 2026-08-08

### Added

- Phase 6 memory: per-project SQLite (`memory.sqlite`) with project_meta/tasks/decisions/events
- Repository dual-write from YAML; summarizer hooked into context builder
- Orchestrator records cycle events and failure decisions
- CLI: `forgeos memory status`, `forgeos memory decisions`, `forgeos memory sync`
- [docs/PHASE6.md](docs/PHASE6.md); [docs/schemas/memory.schema.yaml](docs/schemas/memory.schema.yaml)

### Changed

- Package version `0.7.0`

## [0.6.0] — 2026-08-08

### Added

- Phase 5 verification: richer DoD checks, evidence YAML bundles, failure classifier
- CLI: `forgeos classify`, `forgeos verify`
- Orchestrator stamps failure class into reports and replan artifacts
- [docs/PHASE5.md](docs/PHASE5.md); schemas for verify_result and failure

### Changed

- Package version `0.6.0`

## [0.5.0] — 2026-08-08

### Added

- Phase 4 planning: scheduler, hierarchical planner, replan with attempt cap
- CLI: `forgeos plan`, `forgeos tasks list`, `forgeos run --steps`
- Orchestrator multi-step loop; execute using `task.role`
- [docs/PHASE4.md](docs/PHASE4.md) and [docs/schemas/plan.schema.yaml](docs/schemas/plan.schema.yaml)

### Changed

- Package version `0.5.0`; default plan is a 2-task `.forge` dependency chain

## [0.4.0] — 2026-08-08

### Added

- Phase 3 LLM engine: `LLMClient` protocol, Ollama client, model router, context manager
- CLI: `forgeos llm status`, `forgeos llm complete`, `forgeos run --llm mock|ollama`
- [docs/PHASE3.md](docs/PHASE3.md) and [docs/schemas/llm_request.schema.yaml](docs/schemas/llm_request.schema.yaml)

### Changed

- Package version `0.4.0`; dependency `ollama>=0.4.0`
- Orchestrator/planner typed against `LLMClient` (MockLLM remains default)

## [0.3.0] — 2026-08-08

### Added

- Phase 2 tool engine: registry dispatch, shared `ToolResult`
- Filesystem `edit` / `search` / `tree` / `delete`
- `terminal.execute` with cwd sandbox, timeout, and deny list
- Git `status` / `diff` / `branch` / `commit` (refuse force-push and `reset --hard`)
- `testing.run` (pytest) and `docker.compose_config`
- CLI: `forgeos tools list`, `forgeos tools exec`, `forgeos run --tool-demo`
- Role YAML Phase 2 tool allowlists; [docs/schemas/tool_action.schema.yaml](docs/schemas/tool_action.schema.yaml)
- [docs/PHASE2.md](docs/PHASE2.md)

### Changed

- Package version `0.3.0`; executor dispatches via tool registry

## [0.2.0] — 2026-08-08

### Added

- Phase 1 core engine: CLI (`init` / `run` / `status`), world state, task graph
- Role YAML loader with allowlist enforcement
- One PLAN → ACT → OBSERVE → VERIFY cycle with MockLLM
- Minimal filesystem tool; reports under `.forge/reports/`
- Pytest suite for core paths
- [docs/PHASE1.md](docs/PHASE1.md)

### Changed

- Package version `0.2.0`; `ceo` role allows `filesystem.read` / `filesystem.write` for `.forge/**` writes

## [0.1.1] — 2026-08-08

### Added

- Phase 0.5 preflight contracts: engine layout, model routing, phases map
- JSON/YAML schemas for world state, task, decision, role policy
- Machine-readable `roles/*.yaml` policies (11 roles)
- `forgeos` package skeleton and `pyproject.toml`
- `projects/` sandbox root

### Clarified

- `API_VERSIONING.md` and `DOCKER.md` apply to managed apps, not engine Phase 1 prerequisites
- `release/0.1.0` remains the freeze for tag `v0.1.0`; `v0.1.1` is a patch on `main` only

## [0.1.0] — 2026-08-08

### Added

- Phase 0 Ollama benchmark harness (`benchmarks/phase0`)
- System architecture documentation pack under `docs/`
- Tag `v0.1.0` / branch `release/0.1.0`
