# Phase 13 — Autonomy Stretch (v1.5.0)

## Shipped

- Safety-net template **`full-pipeline`**: CEO → PM → Architect → Backend → QA → Docs → DevOps → Reporter
- LLM-first planning prompt for autonomy goals; validate → template fallback unchanged
- Classify uses **stderr/stdout** + stronger Docker `env` signals
- Replan stops `ops-002-fix-N` chains: hard classes (`env`/`permission`/`timeout`) **BLOCK** without fix; nested `-fix-` never spawn another fix; soft classes get **at most one** fix report
- **`ResourceGovernor`**: unload Ollama model after plan/run; `num_ctx` on router options; prompt budget shrinks under VRAM pressure (≥85%)

## Deferred

- Making Ollama the default CLI backend
- Full UI/UX + database design-kit generation in the seed graph
- Class-aware auto-retry of `docker.compose_up` without human approval
- Cloud deploy / Redis / auth / ORM

## Usage

```powershell
forgeos init auto-demo
forgeos plan auto-demo --template full-pipeline --force
forgeos tasks list auto-demo

# With Ollama (templates still safety net if JSON fails):
forgeos plan auto-demo --llm ollama --template full-pipeline --force
```
