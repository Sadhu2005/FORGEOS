"""FORGEOS Phase 0 benchmark runner.

Runs the fixed prompt set (see ``prompts.py``) against one or more local
Ollama models, records tokens/sec, time-to-first-token, and CPU/RAM/VRAM
deltas for every run, and writes the raw measurements to
``benchmarks/phase0/results/<timestamp>.json``.

Usage:
    python -m benchmarks.phase0.bench
    python -m benchmarks.phase0.bench --models qwen3:4b --runs-per-prompt 3
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import ollama

from benchmarks.phase0 import system_metrics
from benchmarks.phase0.prompts import PROMPTS, BenchmarkPrompt

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_MODELS = ["qwen3:4b", "qwen2.5-coder:7b"]
DEFAULT_RUNS_PER_PROMPT = 2
DEFAULT_HOST = "http://localhost:11434"


def _get(obj, name):
    """Support both dict-style and attribute-style Ollama response objects."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


@dataclass
class RunResult:
    model: str
    prompt_id: str
    category: str
    run_index: int
    ttft_s: float | None
    total_time_s: float
    prompt_tokens: int | None
    eval_tokens: int | None
    tokens_per_sec: float | None
    ram_before_mb: float
    ram_after_mb: float
    vram_before_mb: float | None
    vram_after_mb: float | None
    cpu_percent_after: float
    response_chars: int


def _run_once(
    client: ollama.Client, model: str, prompt: BenchmarkPrompt, run_index: int
) -> RunResult:
    before = system_metrics.take_snapshot(cpu_interval=0.0)

    start = time.perf_counter()
    first_token_at: float | None = None
    text_chars = 0
    final_chunk = None

    stream = client.generate(model=model, prompt=prompt.prompt, stream=True)
    for chunk in stream:
        piece = _get(chunk, "response") or ""
        if first_token_at is None and piece:
            first_token_at = time.perf_counter()
        text_chars += len(piece)
        if _get(chunk, "done"):
            final_chunk = chunk

    end = time.perf_counter()
    after = system_metrics.take_snapshot(cpu_interval=0.3)

    eval_count = _get(final_chunk, "eval_count")
    eval_duration = _get(final_chunk, "eval_duration")
    prompt_eval_count = _get(final_chunk, "prompt_eval_count")

    tokens_per_sec = None
    if eval_count and eval_duration:
        tokens_per_sec = eval_count / (eval_duration / 1e9)

    return RunResult(
        model=model,
        prompt_id=prompt.id,
        category=prompt.category,
        run_index=run_index,
        ttft_s=(first_token_at - start) if first_token_at else None,
        total_time_s=end - start,
        prompt_tokens=prompt_eval_count,
        eval_tokens=eval_count,
        tokens_per_sec=tokens_per_sec,
        ram_before_mb=before.ram_used_mb,
        ram_after_mb=after.ram_used_mb,
        vram_before_mb=before.vram_used_mb,
        vram_after_mb=after.vram_used_mb,
        cpu_percent_after=after.cpu_percent,
        response_chars=text_chars,
    )


def _warm_up(client: ollama.Client, model: str) -> float:
    """Load the model into memory; return load duration in seconds.

    Discarded from the steady-state per-prompt numbers so cold-load time
    doesn't skew tokens/sec on the first real prompt.
    """
    start = time.perf_counter()
    response = client.generate(model=model, prompt="Say OK.", stream=False)
    load_duration = _get(response, "load_duration")
    if load_duration:
        return load_duration / 1e9
    return time.perf_counter() - start


def run_benchmark(models: list[str], runs_per_prompt: int, host: str) -> dict:
    client = ollama.Client(host=host)

    results: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "cpu": system_metrics.cpu_name(),
            "gpu": system_metrics.gpu_name(),
            "gpu_available": system_metrics.gpu_available(),
        },
        "runs_per_prompt": runs_per_prompt,
        "models": {},
    }

    for model in models:
        print(f"\n=== {model} ===")
        print("Warming up (loading model into memory)...")
        load_duration_s = _warm_up(client, model)
        print(f"  load_duration: {load_duration_s:.2f}s")

        model_runs: list[dict] = []
        for prompt in PROMPTS:
            for run_index in range(1, runs_per_prompt + 1):
                print(
                    f"  [{prompt.category}] {prompt.id} "
                    f"(run {run_index}/{runs_per_prompt})...",
                    end=" ",
                    flush=True,
                )
                result = _run_once(client, model, prompt, run_index)
                model_runs.append(asdict(result))
                tps = (
                    f"{result.tokens_per_sec:.1f} tok/s"
                    if result.tokens_per_sec
                    else "n/a"
                )
                print(f"{result.total_time_s:.2f}s, {tps}")

        results["models"][model] = {
            "load_duration_s": load_duration_s,
            "runs": model_runs,
        }

    return results


def save_results(results: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{ts}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="FORGEOS Phase 0 model benchmark")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Ollama model tags to benchmark",
    )
    parser.add_argument("--runs-per-prompt", type=int, default=DEFAULT_RUNS_PER_PROMPT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    args = parser.parse_args()

    results = run_benchmark(args.models, args.runs_per_prompt, args.host)
    path = save_results(results)
    print(f"\nSaved raw results to {path}")


if __name__ == "__main__":
    main()
