# Model Routing (Phase 0 lock)

Hardware baseline: Ryzen 5 3600, 16 GB RAM, GTX 1650 4 GB VRAM. One Ollama model loaded at a time.

## Benchmark summary (Phase 0)

| Model | Avg tok/s | Wall-clock behavior |
|---|---|---|
| `qwen3:4b` | ~15 tok/s | Fast tokens, but default **thinking** produces long outputs (high total time) |
| `qwen2.5-coder:7b` | ~6 tok/s | Partial GPU offload; concise answers; better wall-clock for short/coding tasks |

## Locked routing defaults (until re-benchmarked)

| Task class | Model | Notes |
|---|---|---|
| Coding (edit, generate, fix) | `qwen2.5-coder:7b` | Prefer for Frontend/Backend/Database coding turns |
| Simple Q&A / short lookups | `qwen2.5-coder:7b` | Avoids Qwen3 think overhead by default |
| Planning / architecture | `qwen3:4b` with `think: false` preferred for latency; re-evaluate quality in Phase 4 | If think enabled, expect long runs |
| Warmup / load | Single active model | Unload previous before switching |

## Resource rules

- Never load two models concurrently.
- Prefer switching models only at role/task boundaries, not mid-tool-loop.
- If VRAM/RAM pressure rises: shrink context first, then fall back to the smaller model.

## Implementation note

`forgeos.llm.model_router` (Phase 3, shipped in `v0.4.0`) encodes these defaults and allows routing overrides via constructor. Host override: `FORGEOS_OLLAMA_HOST` (default `http://127.0.0.1:11434`). Use `forgeos llm status` / `forgeos run --llm ollama` to exercise the live path; tests default to `MockLLM`.
