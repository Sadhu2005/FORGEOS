from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.llm.base import LLMError
from forgeos.llm.mock import MockLLM
from forgeos.planning.planner import HierarchicalPlanner
from forgeos.planning.task_graph import Task, TaskGraph
from forgeos.planning.validate import load_role_allowed_tools, validate_llm_tasks
from forgeos.scaffold import scaffold_fastapi_health


def test_validate_accepts_ceo_write(workspace: Path) -> None:
    roles = workspace / "roles"
    tasks = [
        Task(
            id="t1",
            description="note",
            status="READY",
            role="ceo",
            action={"tool": "filesystem.write", "path": ".forge/reports/x.md", "content": "x"},
        )
    ]
    assert validate_llm_tasks(tasks, roles) is not None
    assert "ceo" in load_role_allowed_tools(roles)


def test_validate_rejects_unknown_role(workspace: Path) -> None:
    tasks = [
        Task(
            id="t1",
            description="bad",
            status="READY",
            role="not_a_role",
            action={"tool": "filesystem.write", "path": "x", "content": "x"},
        )
    ]
    assert validate_llm_tasks(tasks, workspace / "roles") is None


def test_validate_rejects_tool_not_allowed(workspace: Path) -> None:
    tasks = [
        Task(
            id="t1",
            description="bad",
            status="READY",
            role="ceo",
            action={"tool": "docker.compose_up", "compose_file": "docker/docker-compose.yml"},
        )
    ]
    assert validate_llm_tasks(tasks, workspace / "roles") is None


class RaisingLLM:
    call_count = 0

    def complete(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        raise LLMError("timed out")


class GarbageLLM:
    call_count = 0

    def complete(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        return "not json at all"


def test_planner_fallback_on_llm_error(workspace: Path) -> None:
    root = ws.create_project(workspace, "fb1")
    graph = TaskGraph()
    HierarchicalPlanner(RaisingLLM()).ensure_plan(
        "Create a Python FastAPI project with a /health endpoint and tests",
        graph,
        project_root=root,
        roles_dir=workspace / "roles",
    )
    assert graph.get("arch-001") is not None or graph.get("be-003") is not None


def test_planner_fallback_on_garbage_json(workspace: Path) -> None:
    root = ws.create_project(workspace, "fb2")
    graph = TaskGraph()
    HierarchicalPlanner(GarbageLLM()).ensure_plan(
        "write hello report",
        graph,
        project_root=root,
        roles_dir=workspace / "roles",
    )
    assert graph.get("task-001") is not None


def test_planner_mock_fastapi_unchanged(workspace: Path) -> None:
    root = ws.create_project(workspace, "fb3")
    graph = TaskGraph()
    HierarchicalPlanner(MockLLM()).ensure_plan(
        "Create a Python FastAPI project with a /health endpoint and tests",
        graph,
        project_root=root,
        roles_dir=workspace / "roles",
    )
    assert graph.get("arch-001") is not None


def test_scaffold_includes_api_ping(workspace: Path) -> None:
    root = ws.create_project(workspace, "ping1")
    scaffold_fastapi_health(root)
    main = (root / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert "/api/v1/ping" in main
    tests = (root / "backend" / "tests" / "test_health.py").read_text(encoding="utf-8")
    assert "test_api_ping" in tests
    assert "/api/v1/ping" in (root / "docs" / "API.md").read_text(encoding="utf-8")
