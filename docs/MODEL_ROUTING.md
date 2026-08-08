# Model Routing (Phase 0 + Phase 11)

Hardware baseline: Ryzen 5 3600, 16 GB RAM, GTX 1650 4 GB VRAM. One Ollama model loaded at a time.

## Benchmark summary (Phase 0)

| Model | Avg tok/s | Wall-clock behavior |
|---|---|---|
| `qwen3:4b` | ~15 tok/s | Fast tokens, but default **thinking** produces long outputs (high total time) |
| `qwen2.5-coder:7b` | ~6 tok/s | Partial GPU offload; concise answers; better wall-clock for short/coding tasks |

## Locked routing defaults (Phase 11)

| Task class | Model | Notes |
|---|---|---|
| Coding (edit, generate, fix) | `qwen2.5-coder:7b` | Prefer for Frontend/Backend/Database coding turns |
| Simple Q&A / short lookups | `qwen2.5-coder:7b` | Avoids Qwen3 think overhead by default |
| Planning / task JSON | `qwen2.5-coder:7b` | **Phase 11:** plan JSON; `think: false` + `num_predict` cap; timeout → seed template |
| Architecture prose (future) | `qwen3:4b` candidate | Not used for `forgeos plan` JSON until think/latency fixed |
| Warmup / load | Single active model | Unload previous before switching |

## Resource rules

- Never load two models concurrently.
- Prefer switching models only at role/task boundaries, not mid-tool-loop.
- If VRAM/RAM pressure rises: shrink context first, then fall back to the smaller model.
- Generate timeout: `FORGEOS_OLLAMA_TIMEOUT` (default **120** seconds).

## Phase 13 ResourceGovernor

`forgeos.llm.governor.ResourceGovernor` implements the shrink/unload side of these rules:

- Unload current model after `plan` / `run` (best-effort `keep_alive=0`)
- `num_ctx`: planning **2048**, coding **4096** (via `ModelRouter.options_for`)
- Prompt budget: default ~8000 chars; shrinks to **4000** when VRAM used ≥ **85%** (`nvidia-smi`)

See [PHASE13.md](PHASE13.md).

## Implementation note

`forgeos.llm.model_router` encodes routing defaults. Host: `FORGEOS_OLLAMA_HOST` (default `http://127.0.0.1:11434`). Use `forgeos llm status` / `forgeos plan --llm ollama`; tests default to `MockLLM`. See [PHASE11.md](PHASE11.md) and [PHASE13.md](PHASE13.md).
