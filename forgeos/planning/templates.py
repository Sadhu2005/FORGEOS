"""Seed TaskGraph templates for hierarchical planning."""

from __future__ import annotations

from pathlib import Path

from forgeos.planning.task_graph import Task


def is_fastapi_health_goal(goal: str) -> bool:
    g = goal.lower()
    return ("fastapi" in g and "health" in g) or (
        "fastapi" in g and "/health" in g
    ) or ("health endpoint" in g and "fastapi" in g)


def fastapi_scaffold_present(project_root: Path | None) -> bool:
    if project_root is None:
        return False
    return (project_root / "backend" / "app" / "main.py").is_file()


def ceo_report_template(goal: str) -> list[Task]:
    """Phase 4 default: CEO writes .forge/reports stubs."""
    return [
        Task(
            id="task-001",
            description=f"Write phase note for goal: {goal}",
            status="READY",
            role="ceo",
            priority=10,
            verification=["file exists", "file is non-empty"],
            action={
                "tool": "filesystem.write",
                "path": ".forge/reports/phase.md",
                "content": (
                    f"# FORGEOS Phase 4 plan note\n\nGoal: {goal}\n\n"
                    "Status: phase recorded.\n"
                ),
            },
        ),
        Task(
            id="task-002",
            description=f"Write hello report for goal: {goal}",
            status="PROPOSED",
            role="ceo",
            priority=20,
            dependencies=["task-001"],
            verification=["file exists", "file is non-empty"],
            action={
                "tool": "filesystem.write",
                "path": ".forge/reports/hello.md",
                "content": (
                    f"# FORGEOS Phase 4 stub report\n\nGoal: {goal}\n\n"
                    "Status: cycle completed.\n"
                ),
            },
        ),
    ]


def fastapi_health_full_template(goal: str) -> list[Task]:
    """Multi-role FastAPI /health seed graph (backend-only)."""
    return [
        Task(
            id="arch-001",
            description="Document FastAPI health architecture",
            status="READY",
            role="software_architect",
            priority=10,
            verification=["file exists", "file is non-empty", "contains:FastAPI"],
            action={
                "tool": "filesystem.write",
                "path": "docs/ARCHITECTURE.md",
                "content": (
                    "# Architecture\n\n"
                    "Managed FastAPI health demo.\n\n"
                    "## Stack\n\n- FastAPI with GET /health\n"
                    "- pytest\n- Docker Compose (backend-only)\n\n"
                    f"Goal: {goal}\n"
                ),
            },
        ),
        Task(
            id="be-001",
            description="Implement FastAPI /health and /api/v1/ping",
            status="PROPOSED",
            role="backend",
            priority=20,
            dependencies=["arch-001"],
            verification=["file exists", "contains:health", "contains:/api/v1/ping"],
            action={
                "tool": "filesystem.write",
                "path": "backend/app/main.py",
                "content": (
                    '"""Minimal FastAPI app with /health and /api/v1/ping."""\n\n'
                    "from fastapi import FastAPI\n\n"
                    'app = FastAPI(title="FORGEOS managed demo")\n\n\n'
                    '@app.get("/health")\n'
                    "def health() -> dict[str, str]:\n"
                    '    return {"status": "ok"}\n\n\n'
                    '@app.get("/api/v1/ping")\n'
                    "def ping() -> dict[str, str]:\n"
                    '    return {"ok": "true", "api": "v1"}\n'
                ),
            },
        ),
        Task(
            id="be-002",
            description="Add health tests and requirements",
            status="PROPOSED",
            role="backend",
            priority=30,
            dependencies=["be-001"],
            verification=["file exists"],
            action={
                "tool": "filesystem.write",
                "path": "backend/tests/test_health.py",
                "content": (
                    '"""Health endpoint tests."""\n\n'
                    "from fastapi.testclient import TestClient\n\n"
                    "from app.main import app\n\n"
                    "client = TestClient(app)\n\n\n"
                    "def test_health() -> None:\n"
                    '    response = client.get("/health")\n'
                    "    assert response.status_code == 200\n"
                    '    assert response.json()["status"] == "ok"\n'
                ),
            },
        ),
        Task(
            id="be-003",
            description="Run backend pytest suite",
            status="PROPOSED",
            role="backend",
            priority=40,
            dependencies=["be-002"],
            verification=["pytest_pass", "exit_code:0"],
            action={
                "tool": "testing.run",
                "args": ["-q"],
                "cwd": "backend",
            },
        ),
        Task(
            id="ops-001",
            description="Add Dockerfile and compose for backend",
            status="PROPOSED",
            role="devops",
            priority=50,
            dependencies=["be-003"],
            verification=["file exists"],
            action={
                "tool": "filesystem.write",
                "path": "docker/docker-compose.yml",
                "content": (
                    "services:\n"
                    "  backend:\n"
                    "    build:\n"
                    "      context: ..\n"
                    "      dockerfile: docker/Dockerfile.backend\n"
                    "    ports:\n"
                    '      - "8000:8000"\n'
                    "    healthcheck:\n"
                    '      test: ["CMD", "python", "-c", '
                    "\"import urllib.request; "
                    "urllib.request.urlopen('http://127.0.0.1:8000/health')\"]\n"
                    "      interval: 5s\n"
                    "      timeout: 3s\n"
                    "      retries: 5\n"
                ),
            },
        ),
        Task(
            id="ops-002",
            description="Start compose stack (requires approval)",
            status="PROPOSED",
            role="devops",
            priority=60,
            dependencies=["ops-001"],
            verification=["exit_code:0"],
            action={
                "tool": "docker.compose_up",
                "compose_file": "docker/docker-compose.yml",
            },
        ),
        Task(
            id="qa-001",
            description="QA re-run tests and write report",
            status="PROPOSED",
            role="qa",
            priority=70,
            dependencies=["ops-002"],
            verification=["file exists", "file is non-empty"],
            action={
                "tool": "filesystem.write",
                "path": ".forge/reports/qa-fastapi-health.md",
                "content": (
                    "# QA report — FastAPI /health\n\n"
                    f"Goal: {goal}\n\n"
                    "Acceptance: pytest green; compose_up approved and executed.\n"
                    "Result: PASS (evidence in evidence-*.yaml).\n"
                ),
            },
        ),
        Task(
            id="doc-001",
            description="Update README with /health run instructions",
            status="PROPOSED",
            role="documentation",
            priority=80,
            dependencies=["qa-001"],
            verification=["file exists", "contains:/health"],
            action={
                "tool": "filesystem.write",
                "path": "README.md",
                "content": (
                    "# Managed FastAPI health demo\n\n"
                    f"Goal: {goal}\n\n"
                    "## Health\n\n"
                    "`GET /health` → `{\"status\": \"ok\"}`\n\n"
                    "```bash\n"
                    "cd backend && pytest -q\n"
                    "uvicorn app.main:app --port 8000\n"
                    "curl http://127.0.0.1:8000/health\n"
                    "```\n"
                ),
            },
        ),
    ]


def fastapi_health_short_template(goal: str) -> list[Task]:
    """When scaffold already present: verify + compose + docs."""
    return [
        Task(
            id="be-003",
            description="Verify backend pytest suite",
            status="READY",
            role="backend",
            priority=10,
            verification=["pytest_pass", "exit_code:0"],
            action={
                "tool": "testing.run",
                "args": ["-q"],
                "cwd": "backend",
            },
        ),
        Task(
            id="ops-001",
            description="Validate compose file present for backend",
            status="PROPOSED",
            role="devops",
            priority=20,
            dependencies=["be-003"],
            verification=["file exists", "contains:backend"],
            action={
                "tool": "filesystem.read",
                "path": "docker/docker-compose.yml",
            },
        ),
        Task(
            id="ops-002",
            description="Start compose stack (requires approval)",
            status="PROPOSED",
            role="devops",
            priority=30,
            dependencies=["ops-001"],
            verification=["exit_code:0"],
            action={
                "tool": "docker.compose_up",
                "compose_file": "docker/docker-compose.yml",
            },
        ),
        Task(
            id="qa-001",
            description="QA report for scaffolded FastAPI health",
            status="PROPOSED",
            role="qa",
            priority=40,
            dependencies=["ops-002"],
            verification=["file exists", "file is non-empty"],
            action={
                "tool": "filesystem.write",
                "path": ".forge/reports/qa-fastapi-health.md",
                "content": (
                    "# QA report — FastAPI /health (scaffolded)\n\n"
                    f"Goal: {goal}\n\nResult: PASS.\n"
                ),
            },
        ),
        Task(
            id="doc-001",
            description="Confirm README documents /health",
            status="PROPOSED",
            role="documentation",
            priority=50,
            dependencies=["qa-001"],
            verification=["file exists", "contains:/health"],
            action={
                "tool": "filesystem.write",
                "path": "README.md",
                "content": (
                    "# Managed FastAPI health demo\n\n"
                    f"Goal: {goal}\n\n"
                    "`GET /health` → ok\n\n"
                    "See docs/API.md.\n"
                ),
            },
        ),
    ]


def select_template(
    goal: str,
    *,
    template: str | None = None,
    project_root: Path | None = None,
) -> list[Task]:
    """Choose seed graph from explicit template name or goal keywords."""
    name = (template or "").strip().lower()
    if name in ("default", "ceo", "ceo-report"):
        return ceo_report_template(goal)
    use_fastapi = name in ("fastapi-health", "fastapi_health", "fastapi") or (
        not name and is_fastapi_health_goal(goal)
    )
    if use_fastapi:
        if fastapi_scaffold_present(project_root):
            return fastapi_health_short_template(goal)
        return fastapi_health_full_template(goal)
    return ceo_report_template(goal)
