# Phase 3 — What shipped

Tag: `v0.4.0`  
Branch (during development): `feature/phase3-llm-engine`

## Shipped

- `LLMClient` protocol and `LLMError` ([forgeos/llm/base.py](../forgeos/llm/base.py))
- `MockLLM` adapted to the protocol (default for tests / `forgeos run --llm mock`)
- `OllamaClient`: generate, list models, unload (`keep_alive=0`), one-at-a-time concurrency guard
- `ModelRouter` + `RoutedLLM` encoding [MODEL_ROUTING.md](MODEL_ROUTING.md) defaults; `think: false` for planning/qwen3
- `ContextManager` with ~8k character budget truncation
- Orchestrator builds context when using Ollama; stub planner still emits the Phase 1 write-file task
- CLI: `forgeos llm status`, `forgeos llm complete`, `forgeos run --llm mock|ollama`
- Schema: [schemas/llm_request.schema.yaml](schemas/llm_request.schema.yaml)
- Pytest coverage with mocked Ollama (no daemon required in CI)

## Deferred

| Capability | Phase |
|---|---|
| Hierarchical planner / replan / next-task selection | 4 |
| Rich verification / failure taxonomy | 5 |
| SQLite memory | 6 |
| Approval gates / audit / git checkpoint | 7 |
| Dashboard | 9 |

## Demo

```powershell
pip install -e ".[dev]"
forgeos llm status
forgeos llm complete --prompt "Say OK." --task-class simple
forgeos init demo
forgeos run demo --llm mock --goal "write hello report"
forgeos run demo --llm ollama --goal "write hello report"
```
