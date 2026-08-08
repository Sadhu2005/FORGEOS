"""Minimal FastAPI /health managed-app scaffold under a project root."""

from __future__ import annotations

from pathlib import Path

MAIN_PY = '''"""Minimal FastAPI app with /health."""

from fastapi import FastAPI

app = FastAPI(title="FORGEOS managed demo")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
'''

TEST_HEALTH = '''"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
'''

REQUIREMENTS = """fastapi>=0.110
uvicorn[standard]>=0.27
httpx>=0.27
pytest>=8.0
"""

DOCKERFILE = """FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/app /app/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

COMPOSE = """services:
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 5s
      timeout: 3s
      retries: 5
"""

ARCHITECTURE = """# Architecture

Managed FastAPI health demo scaffolded by FORGEOS.

## Stack

- FastAPI backend with `GET /health`
- pytest + httpx TestClient
- Docker Compose (backend-only)

No frontend, Postgres, or Redis required for this demo.
"""

API_MD = """# API

## GET /health

Returns JSON `{"status": "ok"}` when the service is up.
"""

README = """# {name}

FORGEOS-managed FastAPI health demo.

## Local tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

## Run API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
curl http://127.0.0.1:8000/health
```

## Docker Compose

```bash
docker compose -f docker/docker-compose.yml up -d --build
curl http://127.0.0.1:8000/health
```
"""

CHANGELOG = """# Changelog

## 0.1.0

- Scaffolded FastAPI `/health` demo via `forgeos init --scaffold`.
"""

BACKEND_INIT = '"""Backend package."""\n'
APP_INIT = '"""FastAPI application package."""\n'


def scaffold_fastapi_health(project_root: Path, *, name: str | None = None) -> list[Path]:
    """Write minimal backend + docker + docs tree. Returns written paths."""
    root = project_root.resolve()
    proj_name = name or root.name
    written: list[Path] = []

    def write(rel: str, content: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)

    write("backend/__init__.py", BACKEND_INIT)
    write("backend/app/__init__.py", APP_INIT)
    write("backend/app/main.py", MAIN_PY)
    write("backend/tests/__init__.py", "")
    write("backend/tests/test_health.py", TEST_HEALTH)
    write("backend/requirements.txt", REQUIREMENTS)
    write("docker/Dockerfile.backend", DOCKERFILE)
    write("docker/docker-compose.yml", COMPOSE)
    write("docs/ARCHITECTURE.md", ARCHITECTURE)
    write("docs/API.md", API_MD)
    write("README.md", README.format(name=proj_name))
    write("CHANGELOG.md", CHANGELOG)
    return written
