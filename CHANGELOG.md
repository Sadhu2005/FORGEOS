# Changelog

All notable changes to FORGEOS are documented here.

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
