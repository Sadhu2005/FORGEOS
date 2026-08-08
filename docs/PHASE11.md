# Phase 11 — Ollama + Managed Backend (v1.2.0)

## Shipped

- Planning route uses `qwen2.5-coder:7b` (not hanging `qwen3:4b` think) with `think: false` + `num_predict` cap
- Ollama generate **timeout** (`FORGEOS_OLLAMA_TIMEOUT`, default 120s) → `LLMError` → planner **seed template** fallback
- LLM task **role/tool allowlist** validation (`forgeos/planning/validate.py`)
- Scaffold `/api/v1/ping` alongside `/health` (+ tests, API.md)
- Dashboard home/project shows Ollama online/offline
- Demo: [docs/demo/OLLAMA_FASTAPI.md](demo/OLLAMA_FASTAPI.md), `scripts/demo_ollama_fastapi.ps1`

## Deferred

- PostgreSQL / Redis compose profile (**Postgres profile shipped in Phase 11b** — see [PHASE11B.md](PHASE11B.md))
- Next.js frontend (**shipped in Phase 12** — see [PHASE12.md](PHASE12.md))
- Full CEO→…→Reporter autonomy without templates
- Cloud deploy
- Making Ollama the default CLI backend
- Using `qwen3:4b` for plan JSON (revisit after think/latency fixes)

## Spike resolution

Phase 10 spike: `plan --llm ollama` with `qwen3:4b` hung. Fixed by routing planning → coder + timeout + template fallback.

## Demo

Mock path unchanged. Ollama:

```powershell
forgeos plan demo --goal "Create a Python FastAPI project with a /health endpoint and tests" --template fastapi-health --llm ollama --force
```
