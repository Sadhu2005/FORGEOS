# FORGEOS Engine Layout

Target Python package layout for the engine (filled starting Phase 1). Paths under `forgeos/` are code; `roles/` and `docs/schemas/` are contracts loaded by that code.

```text
FORGEOS/
├── forgeos/
│   ├── __init__.py
│   ├── cli.py                 # Phase 1+: `forge` / `python -m forgeos`
│   ├── core/
│   │   ├── orchestrator.py
│   │   ├── observer.py
│   │   ├── executor.py
│   │   ├── verifier.py
│   │   └── classifier.py
│   ├── planning/
│   │   ├── planner.py
│   │   ├── task_graph.py
│   │   ├── scheduler.py
│   │   └── replan.py
│   ├── llm/
│   │   ├── base.py            # LLMClient protocol
│   │   ├── mock.py
│   │   ├── ollama_client.py
│   │   ├── model_router.py
│   │   └── context_manager.py
│   ├── tools/
│   │   ├── base.py            # ToolResult
│   │   ├── registry.py        # name → handler dispatch
│   │   ├── filesystem.py
│   │   ├── terminal.py
│   │   ├── git.py
│   │   ├── testing.py
│   │   └── docker.py
│   ├── memory/
│   │   ├── database.py
│   │   ├── repository.py
│   │   └── summarizer.py
│   ├── safety/
│   │   ├── permissions.py
│   │   ├── approval.py
│   │   └── audit.py
│   └── roles/
│       └── loader.py          # loads ../../roles/*.yaml
├── roles/                     # YAML policies (repo root) — see roles/README.md
├── docs/
│   └── schemas/               # world_state, task, decision, role_policy, tool_action
├── projects/                  # managed app sandboxes
├── benchmarks/
└── pyproject.toml
```

## Module ownership by phase

| Package | Phase | Status |
|---|---|---|
| `forgeos.core`, CLI, world state I/O | 1 | **Present** (`v0.2.0`) |
| `forgeos.planning` (minimal task graph + stub planner) | 1 | **Present** (expanded in Phase 4) |
| `forgeos.roles.loader` | 1 | **Present** |
| `forgeos.llm.mock` | 1 | **Present** |
| `forgeos.tools.filesystem` | 1–2 | **Present** (Phase 2: edit/search/tree/delete) |
| `forgeos.tools` (registry, terminal, git, testing, docker) | 2 | **Present** (`v0.3.0`) |
| `forgeos.llm` (Ollama, router, context) | 3 | **Present** (`v0.4.0`) |
| `forgeos.planning` (scheduler, hierarchical planner, replan) | 4 | **Present** (`v0.5.0`) |
| `forgeos.core.verifier` + `classifier` | 5 | **Present** (`v0.6.0`) |
| `forgeos.memory` | 6 | Pending |
| `forgeos.safety` | 7 | Pending |
| Engineering intelligence extras | 8 | Pending |
| Dashboard (separate UI) | 9 | Pending |

## Rules

- One LLM invocation at a time (see [ARCHITECTURE.md](ARCHITECTURE.md)).
- Role policies come from `roles/*.yaml`, validated against [schemas/role_policy.schema.yaml](schemas/role_policy.schema.yaml).
- Managed apps never import from `forgeos` as a library dependency of production app code; FORGEOS drives them from outside via tools.
