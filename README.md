# FORGEOS

**Local AI Engineering Operating System.**

FORGEOS is a single local LLM (run through [Ollama](https://ollama.com)) wrapped in a
software-engineering loop — plan, act, observe, verify, replan — instead of a swarm of
competing agents. Job titles (CEO, PM, Architect, Frontend, QA, …) are **sequential role
policies**, not concurrent processes.

> FORGEOS does not trust the model. It trusts evidence.

## Architecture

System design lives in `docs/` (contracts for later engine phases):

| Document | Topic |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview, loop, world state |
| [docs/ENGINE_LAYOUT.md](docs/ENGINE_LAYOUT.md) | Python package layout for the engine |
| [docs/MODEL_ROUTING.md](docs/MODEL_ROUTING.md) | Phase 0 model routing lock |
| [docs/PHASE1.md](docs/PHASE1.md) | Phase 1 what shipped / deferred |
| [docs/PHASE2.md](docs/PHASE2.md) | Phase 2 tool engine what shipped / deferred |
| [docs/PHASES.md](docs/PHASES.md) | Phase 0–9 map, branches, DoD notes |
| [docs/ROLES.md](docs/ROLES.md) | Eleven role policies (human-readable) |
| [roles/](roles/) | Machine-readable role YAML stubs |
| [docs/schemas/](docs/schemas/) | World state, task, decision, role schemas |
| [docs/GIT_AND_RELEASE.md](docs/GIT_AND_RELEASE.md) | Trunk-based branches, SemVer tags, hotfixes |
| [docs/PROJECT_LAYOUT.md](docs/PROJECT_LAYOUT.md) | Managed project monorepo shape |
| [docs/API_VERSIONING.md](docs/API_VERSIONING.md) | `/api/v1` for managed apps (not engine) |
| [docs/DOCKER.md](docs/DOCKER.md) | Local Compose for managed apps; Ollama on host |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | Goal → report end-to-end pipeline |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

**Runnable today:** Phase 0 benchmark + Phase 1 core CLI + Phase 2 tools (`forgeos tools …`). Ollama is required for Phase 0 benchmarks; engine cycles still use MockLLM until Phase 3.

## Requirements

- Windows (developed/tested on Windows)
- Python 3.12
- For Phase 0 benchmarks: [Ollama](https://ollama.com) on `PATH` and `nvidia-smi` if VRAM metrics are desired

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Phase 1 — Core CLI

```powershell
forgeos init demo
forgeos run demo --goal "write hello report"
forgeos status demo
python -m forgeos --version
pytest
```

Creates `projects/demo/.forge/state.yaml` and a stub cycle report under `.forge/reports/`.

## Phase 2 — Tools CLI

```powershell
forgeos tools list
forgeos tools exec demo --role ceo --tool filesystem.tree --arg max_depth=2
forgeos tools exec demo --role backend --tool git.status
forgeos run demo --tool-demo
```

## Phase 0 — Benchmark

Requires Ollama and benchmark deps (`pip install -r requirements.txt`). Pull models once:

```powershell
ollama pull qwen3:4b
ollama pull qwen2.5-coder:7b
```

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
├── docs/                       # system architecture pack + schemas
├── roles/                      # role policy YAML (loaded in Phase 1+)
├── forgeos/                    # Python package (Phase 1+ core engine)
├── tests/                      # pytest suite
├── projects/                   # managed app sandboxes (gitignored contents)
├── benchmarks/
│   └── phase0/
│       ├── prompts.py          # fixed benchmark prompt set
│       ├── system_metrics.py   # CPU / RAM / VRAM sampling helpers
│       ├── bench.py            # benchmark runner
│       ├── report.py           # results -> terminal + markdown report
│       └── results/            # output directory
├── pyproject.toml
├── CHANGELOG.md
├── requirements.txt
└── README.md
```

Later phases implement the contracts in `docs/` / `roles/` inside `forgeos/` and build on Phase 0 model-routing results. See [docs/PHASES.md](docs/PHASES.md).
