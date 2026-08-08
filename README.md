# FORGEOS

**Local AI Engineering Operating System.**

FORGEOS is a single local LLM (run through [Ollama](https://ollama.com)) wrapped in a
software-engineering loop — plan, act, observe, verify, replan — instead of a swarm of
competing agents. See the project design notes in chat/plan history for the full
architecture. This repository currently contains **Phase 0**: a hardware/model
benchmark used to decide how FORGEOS should route work between models later on.

## Requirements

- Windows with [Ollama](https://ollama.com) installed and on `PATH`
- Python 3.12
- An NVIDIA GPU with `nvidia-smi` available (used for VRAM sampling; the benchmark
  still runs without it, just without VRAM numbers)

## Setup

```powershell
# Create and activate the virtual environment (already created at .venv if you followed setup)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Pull the benchmark models (only needed once)
ollama pull qwen3:4b
ollama pull qwen2.5-coder:7b
```

## Phase 0 — Benchmark

Runs a fixed set of `simple` / `coding` / `planning` prompts against each model,
capturing tokens/sec, time-to-first-token, and CPU/RAM/VRAM deltas.

```powershell
# Run the benchmark (defaults to qwen3:4b and qwen2.5-coder:7b, 2 runs per prompt)
python -m benchmarks.phase0.bench

# Render the latest results as a report (terminal + markdown file)
python -m benchmarks.phase0.report
```

Results are written to `benchmarks/phase0/results/`:

- `<timestamp>.json` — raw per-run measurements (gitignored, regenerate anytime)
- `<timestamp>_report.md` — human-readable summary (kept in git)

## Project layout

```text
FORGEOS/
├── benchmarks/
│   └── phase0/
│       ├── prompts.py          # fixed benchmark prompt set
│       ├── system_metrics.py   # CPU / RAM / VRAM sampling helpers
│       ├── bench.py            # benchmark runner
│       ├── report.py           # results -> terminal + markdown report
│       └── results/            # output directory
├── requirements.txt
└── README.md
```

Later phases (core engine, planner, tool protocol, memory, safety) will build on
whatever this benchmark tells us about model routing, and will land in their own
plans once Phase 0 numbers are in.
