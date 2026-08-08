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
│   │   └── verifier.py
│   ├── planning/
│   │   ├── planner.py
│   │   ├── task_graph.py
│   │   └── scheduler.py
│   ├── llm/
│   │   ├── ollama_client.py
│   │   ├── model_router.py
│   │   └── context_manager.py
│   ├── tools/
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
│   └── schemas/               # world_state, task, decision, role_policy
├── projects/                  # managed app sandboxes
├── benchmarks/
└── pyproject.toml
```

## Module ownership by phase

| Package | Phase |
|---|---|
| `forgeos.core`, basic CLI, world state I/O | 1 |
| `forgeos.tools` | 2 |
| `forgeos.llm` | 3 |
| `forgeos.planning` | 4 |
| Verification depth in `core.verifier` | 5 |
| `forgeos.memory` | 6 |
| `forgeos.safety` | 7 |
| Engineering intelligence extras | 8 |
| Dashboard (separate UI) | 9 |

## Rules

- One LLM invocation at a time (see [ARCHITECTURE.md](ARCHITECTURE.md)).
- Role policies come from `roles/*.yaml`, validated against [schemas/role_policy.schema.yaml](schemas/role_policy.schema.yaml).
- Managed apps never import from `forgeos` as a library dependency of production app code; FORGEOS drives them from outside via tools.
