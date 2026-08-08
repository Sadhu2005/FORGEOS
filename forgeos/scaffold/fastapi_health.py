"""Minimal FastAPI /health + /api/v1/ping managed-app scaffold under a project root."""

from __future__ import annotations

from pathlib import Path

MAIN_PY = '''"""Minimal FastAPI app with /health and /api/v1/ping."""

from __future__ import annotations

import os

from fastapi import FastAPI

app = FastAPI(title="FORGEOS managed demo")


def _database_status() -> str:
    """Return skipped|ok|error based on optional DATABASE_URL."""
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        return "skipped"
    try:
        import psycopg

        with psycopg.connect(url, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return "ok"
    except Exception:
        return "error"


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "FORGEOS managed demo",
        "health": "/health",
        "api": "/api/v1/ping",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": _database_status()}


@app.get("/api/v1/ping")
def ping() -> dict[str, str]:
    return {"ok": "true", "api": "v1"}
'''

TEST_HEALTH = '''"""Health and API ping tests."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "skipped"


def test_health_database_ok() -> None:
    with patch("app.main._database_status", return_value="ok"):
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_health_database_error() -> None:
    with patch("app.main._database_status", return_value="error"):
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "error"


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"] == "/health"


def test_api_ping() -> None:
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json()["ok"] == "true"
    assert response.json()["api"] == "v1"
'''

# Isolate managed-app pytest from the FORGEOS engine pyproject.toml
PYTEST_INI = """[pytest]
pythonpath = .
testpaths = tests
"""

REQUIREMENTS = """fastapi>=0.110
uvicorn[standard]>=0.27
httpx>=0.27
pytest>=8.0
psycopg[binary]>=3.1
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
    environment:
      DATABASE_URL: ${DATABASE_URL:-}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 5s
      timeout: 3s
      retries: 5

  postgres:
    profiles: ["db"]
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: forgeos
      POSTGRES_PASSWORD: forgeos
      POSTGRES_DB: forgeos
    ports:
      - "5432:5432"
    volumes:
      - forgeos_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U forgeos -d forgeos"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  forgeos_pgdata:
"""

ARCHITECTURE = """# Architecture

Managed FastAPI health demo scaffolded by FORGEOS.

## Stack

- FastAPI backend with `GET /health` and `GET /api/v1/ping`
- pytest + httpx TestClient
- Docker Compose (backend always; optional Postgres via profile `db`)

Default compose is backend-only. Enable Postgres with:

```bash
docker compose -f docker/docker-compose.yml --profile db up -d --build
```

No frontend or Redis required for this demo.
"""

ARCHITECTURE_DB = """# Architecture

Managed FastAPI health demo scaffolded by FORGEOS (with optional Postgres).

## Stack

- FastAPI backend with `GET /health` (includes `database` readiness) and `GET /api/v1/ping`
- pytest + httpx TestClient
- Docker Compose: backend + Postgres under profile `db`

```bash
docker compose -f docker/docker-compose.yml --profile db up -d --build
```

Copy `.env.example` to `.env` and set `DATABASE_URL` so `/health` can report `database: ok`.

No frontend or Redis required for this demo.
"""

API_MD = """# API

## GET /health

Returns JSON when the service is up:

```json
{"status": "ok", "database": "skipped"}
```

`database` is `skipped` without `DATABASE_URL`, `ok` when Postgres answers, or `error` on failure.

## GET /api/v1/ping

Versioned API stub. Returns `{"ok": "true", "api": "v1"}`.

See FORGEOS [API_VERSIONING.md](https://github.com/Sadhu2005/FORGEOS/blob/main/docs/API_VERSIONING.md) for `/api/v1` conventions.
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
# http://127.0.0.1:8000/health
# http://127.0.0.1:8000/api/v1/ping
```

## Docker Compose (backend only)

```bash
docker compose -f docker/docker-compose.yml up -d --build
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/ping
```

## Optional Postgres (profile `db`)

```bash
docker compose -f docker/docker-compose.yml --profile db up -d --build
# DATABASE_URL=postgresql://forgeos:forgeos@localhost:5432/forgeos
```
"""

README_DB = """# {name}

FORGEOS-managed FastAPI health demo (Postgres profile ready).

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
# http://127.0.0.1:8000/health  → database: skipped|ok|error
# http://127.0.0.1:8000/api/v1/ping
```

## Docker Compose + Postgres

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml --profile db up -d --build
curl http://127.0.0.1:8000/health
```

Backend-only (no DB):

```bash
docker compose -f docker/docker-compose.yml up -d --build
```
"""

ENV_EXAMPLE = """# Used by backend when checking /health database readiness
DATABASE_URL=postgresql://forgeos:forgeos@localhost:5432/forgeos
"""

CHANGELOG = """# Changelog

## 0.1.0

- Scaffolded FastAPI `/health` + `/api/v1/ping` demo via `forgeos init --scaffold`.
- Optional Compose Postgres profile `db` (Phase 11b).
"""

BACKEND_INIT = '"""Backend package."""\n'
APP_INIT = '"""FastAPI application package."""\n'


def scaffold_fastapi_health(
    project_root: Path,
    *,
    name: str | None = None,
    with_db: bool = False,
) -> list[Path]:
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
    write("backend/pytest.ini", PYTEST_INI)
    write("backend/requirements.txt", REQUIREMENTS)
    write("docker/Dockerfile.backend", DOCKERFILE)
    write("docker/docker-compose.yml", COMPOSE)
    write(
        "docs/ARCHITECTURE.md",
        ARCHITECTURE_DB if with_db else ARCHITECTURE,
    )
    write("docs/API.md", API_MD)
    write(
        "README.md",
        (README_DB if with_db else README).format(name=proj_name),
    )
    write("CHANGELOG.md", CHANGELOG)
    if with_db:
        write(".env.example", ENV_EXAMPLE)
    return written
