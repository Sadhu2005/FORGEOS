from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.dashboard import views
from forgeos.planning.task_graph import Task, TaskGraph


def test_list_projects_and_overview(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()
    root = ws.create_project(tmp_path, "dash1")
    graph = TaskGraph(
        [Task(id="t1", description="x", status="READY", role="ceo")]
    )
    graph.save(ws.tasks_path(root))
    projects = views.list_projects(tmp_path)
    assert any(p["slug"] == "dash1" for p in projects)
    ov = views.project_overview(tmp_path, "dash1")
    assert ov["task_total"] == 1
    assert ov["name"] == "dash1"


def test_render_index_contains_brand(tmp_path: Path) -> None:
    html = views.render(
        "index.html",
        title="FORGEOS",
        projects=[],
        has_projects=False,
        empty_hint="none yet",
    )
    assert "FORGEOS" in html
    assert "none yet" in html
