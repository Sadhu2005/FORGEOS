# Demo — Ollama + FastAPI `/health` (Phase 11)

Uses live Ollama for **plan** JSON. Mock remains the default for CI. If Ollama times out or returns bad JSON, FORGEOS falls back to the `fastapi-health` seed template.

## Prerequisites

```powershell
pip install -e ".[dev]"
ollama list   # need qwen2.5-coder:7b
forgeos llm status
```

Optional: `$env:FORGEOS_OLLAMA_TIMEOUT = "90"`

## Steps

```powershell
forgeos init ollama-demo --scaffold
cd projects\ollama-demo\backend
pip install -r requirements.txt
pytest -q
cd ..\..\..

forgeos plan ollama-demo --goal "Create a Python FastAPI project with a /health endpoint and tests" --template fastapi-health --llm ollama --force
forgeos tasks list ollama-demo

# Run cycles with mock for speed (or --llm ollama for coding turns)
forgeos run ollama-demo --goal "Create a Python FastAPI project with a /health endpoint and tests" --steps 3 --llm mock
```

## Verify API

```powershell
cd projects\ollama-demo\backend
uvicorn app.main:app --port 8000
# http://127.0.0.1:8000/health
# http://127.0.0.1:8000/api/v1/ping
```

## Notes

- Planning model: `qwen2.5-coder:7b` (see [MODEL_ROUTING.md](../MODEL_ROUTING.md)).
- First cold load can take 1–3 minutes; timeout prevents infinite hang.
- Dashboard shows Ollama online/offline at http://127.0.0.1:18080/
