from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.planning.templates import (
    fastapi_next_health_full_template,
    fastapi_next_health_short_template,
    is_fastapi_next_health_goal,
    select_template,
)
from forgeos.scaffold import scaffold_fastapi_health


def test_default_scaffold_has_no_frontend(workspace: Path) -> None:
    root = ws.create_project(workspace, "nofe")
    scaffold_fastapi_health(root)
    assert not (root / "frontend").exists()
    compose = (root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "frontend:" not in compose
    assert "postgres:" in compose
    assert 'profiles: ["db"]' in compose


def test_with_frontend_writes_next_slice(workspace: Path) -> None:
    root = ws.create_project(workspace, "fe1")
    scaffold_fastapi_health(root, with_frontend=True)
    assert (root / "frontend" / "package.json").is_file()
    assert (root / "frontend" / "app" / "page.js").is_file()
    assert (root / "frontend" / "app" / "layout.js").is_file()
    assert (root / "docker" / "Dockerfile.frontend").is_file()
    page = (root / "frontend" / "app" / "page.js").read_text(encoding="utf-8")
    assert "/api/v1/ping" in page
    compose = (root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "frontend:" in compose
    assert "3000:3000" in compose
    assert "BACKEND_URL: http://backend:8000" in compose
    assert "depends_on:" in compose
    assert "Next.js" in (root / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")


def test_cli_init_with_frontend(workspace: Path, capsys) -> None:
    assert main(["init", "fe-cli", "--scaffold", "--with-frontend"]) == 0
    out = capsys.readouterr().out
    assert "Next.js" in out or "frontend" in out.lower()
    root = ws.project_root(workspace, "fe-cli")
    assert (root / "frontend" / "package.json").is_file()
    assert (root / "docker" / "Dockerfile.frontend").is_file()


def test_cli_with_frontend_implies_scaffold(workspace: Path) -> None:
    assert main(["init", "fe-impl", "--with-frontend"]) == 0
    root = ws.project_root(workspace, "fe-impl")
    assert (root / "backend" / "app" / "main.py").is_file()
    assert (root / "frontend" / "app" / "page.js").is_file()


def test_with_frontend_and_db(workspace: Path) -> None:
    root = ws.create_project(workspace, "fe-db")
    scaffold_fastapi_health(root, with_frontend=True, with_db=True)
    assert (root / ".env.example").is_file()
    assert (root / "frontend" / "package.json").is_file()
    compose = (root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "frontend:" in compose
    assert 'profiles: ["db"]' in compose


def test_is_fastapi_next_health_goal() -> None:
    assert is_fastapi_next_health_goal(
        "Create a Next.js frontend with FastAPI /health and ping"
    )
    assert not is_fastapi_next_health_goal(
        "Create a Python FastAPI project with a /health endpoint and tests"
    )


def test_next_full_template_roles_and_ids() -> None:
    tasks = fastapi_next_health_full_template("Next.js FastAPI")
    ids = [t.id for t in tasks]
    assert ids == [
        "arch-001",
        "be-001",
        "be-002",
        "be-003",
        "fe-001",
        "ops-001",
        "ops-002",
        "qa-001",
        "doc-001",
    ]
    assert tasks[4].role == "frontend"
    assert "/api/v1/ping" in (tasks[4].action or {}).get("content", "")


def test_next_short_when_frontend_scaffold_present(workspace: Path) -> None:
    root = ws.create_project(workspace, "fe-short")
    scaffold_fastapi_health(root, with_frontend=True)
    tasks = select_template(
        "Next.js FastAPI health",
        template="fastapi-next-health",
        project_root=root,
    )
    assert [t.id for t in tasks] == [
        "be-003",
        "ops-001",
        "ops-002",
        "qa-001",
        "doc-001",
    ]
    assert fastapi_next_health_short_template("g")[0].id == "be-003"


def test_fastapi_health_unchanged_without_next(workspace: Path) -> None:
    root = ws.create_project(workspace, "fe-reg")
    tasks = select_template(
        "Create a Python FastAPI project with a /health endpoint and tests",
        project_root=root,
    )
    assert tasks[0].id == "arch-001"
    assert not any(t.id == "fe-001" for t in tasks)
