# Phase 11 — Ollama + richer managed backend (draft)

**Status:** planned (not started)  
**Proposed tag:** `v1.2.0`  
**Branch (when started):** `feature/phase11-ollama-managed-backend`

Builds on Phase 10 (`v1.1.x`): keep MockLLM as default CLI; harden the **live Ollama** path and deepen the managed FastAPI demo without requiring Next.js yet.

## Goals

1. **Ollama demo path** for the canonical FastAPI `/health` goal is documented, tested, and reliable (template fallback + role/tool validation when the model returns JSON).
2. **Richer backend scaffold** (optional flag or template): minimal `/api/v1` stub + health, still backend-only Compose.
3. **Optional Postgres** behind a compose profile or `--with-db` (not required for `/health`).
4. Clear PHASE11 shipped/deferred; CHANGELOG `1.2.0`.

## Non-goals (still deferred)

- Next.js frontend / full monorepo UI (candidate Phase 12)
- Full CEO→…→Reporter autonomy without templates
- Cloud / production deploy
- Making Ollama the default CLI backend

## Locked direction (from post-v1.1 options)

| Option | Phase 11? |
|---|---|
| A — Patch polish | Done as `v1.1.1` |
| B — Richer managed backend | **In scope** |
| C — Ollama path harden | **In scope** |
| D — Next.js | Deferred |
| E — Full autonomy | Deferred |

## Draft DoD

1. `forgeos plan … --llm ollama --template fastapi-health` succeeds with Ollama running (`qwen3:4b` / router defaults).
2. Invalid LLM task JSON falls back to seed template; roles/tools still validated.
3. `forgeos init name --scaffold` (or `--scaffold api`) includes `/api/v1` ping + `/health`.
4. Pytest green; demo doc section for Ollama; no regression on mock path.
5. Merged to `main`, tagged `v1.2.0`, `release/1.2.0` pushed.

## Suggested first implementation slice

1. Integration test: Ollama available → skip if down; else plan fastapi-health.
2. Planner: validate LLM tasks against allowlists before accept.
3. Scaffold: `GET /api/v1/ping` + OpenAPI note in `docs/API.md`.
4. Docs: `docs/demo/OLLAMA_FASTAPI.md` + PHASE11.md shipped checklist.

## Open decisions (resolve at kickoff)

- Scaffold flag: extend `--scaffold` vs `--scaffold fastapi-api`
- Postgres: compose profile `db` vs separate template
- Whether dashboard shows “Ollama online” in project overview

## Spike notes (2026-08-08)

- `forgeos llm status`: Ollama reachable; models `qwen2.5-coder:7b`, `qwen3:4b` present.
- `forgeos plan … --llm ollama` with planning route `qwen3:4b` **hung for 5+ minutes** with no task graph written (likely think/long generation). Kill and fall back to mock for demos until Phase 11 adds timeout + `think: false` / coder model for plan JSON.
- Short `qwen2.5-coder:7b` complete should be preferred for plan JSON generation in v1.2.0.
