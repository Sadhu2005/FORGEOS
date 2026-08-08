from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.planning.planner import HierarchicalPlanner, default_template
from forgeos.planning.task_graph import TaskGraph
from forgeos.planning.templates import (
    fastapi_health_full_template,
    fastapi_health_short_template,
    is_fastapi_health_goal,
    select_template,
)
from forgeos.scaffold import scaffold_fastapi_health


def test_is_fastapi_health_goal() -> None:
    assert is_fastapi_health_goal(
        "Create a Python FastAPI project with a /health endpoint and tests"
    )
    assert not is_fastapi_health_goal("write hello report")


def test_full_template_roles_and_ids() -> None:
    tasks = fastapi_health_full_template("FastAPI /health")
    ids = [t.id for t in tasks]
    assert ids == [
        "arch-001",
        "be-001",
        "be-002",
        "be-003",
        "ops-001",
        "ops-002",
        "qa-001",
        "doc-001",
    ]
    assert tasks[0].role == "software_architect"
    assert tasks[1].role == "backend"
    assert tasks[4].role == "devops"
    assert tasks[6].role == "qa"
    assert tasks[7].role == "documentation"
    assert "ceo" not in {t.role for t in tasks}


def test_short_template_when_scaffold_present(workspace: Path) -> None:
    root = ws.create_project(workspace, "scaf")
    scaffold_fastapi_health(root)
    tasks = select_template(
        "Create FastAPI /health endpoint",
        project_root=root,
    )
    assert tasks[0].id == "be-003"
    assert any(t.id == "ops-002" for t in tasks)


def test_default_template_keeps_ceo_for_non_fastapi() -> None:
    tasks = default_template("hello world")
    assert tasks[0].id == "task-001"
    assert tasks[0].role == "ceo"


def test_planner_ensure_plan_fastapi(workspace: Path) -> None:
    root = ws.create_project(workspace, "planfa")
    goal = "Create a Python FastAPI project with a /health endpoint and tests"
    graph = TaskGraph()
    HierarchicalPlanner().ensure_plan(goal, graph, project_root=root)
    assert graph.get("arch-001") is not None
    assert graph.get("be-001") is not None
    assert graph.get("task-001") is None


def test_explicit_default_template_flag() -> None:
    tasks = select_template("Create FastAPI /health", template="default")
    assert tasks[0].id == "task-001"


def test_short_template_ids() -> None:
    tasks = fastapi_health_short_template("goal")
    assert [t.id for t in tasks] == ["be-003", "ops-001", "ops-002", "qa-001", "doc-001"]
