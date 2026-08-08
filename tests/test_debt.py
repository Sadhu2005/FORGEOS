from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.intelligence.debt import debt_path, scan
from forgeos.planning.task_graph import Task, TaskGraph


def test_debt_scan_todos_and_blocked(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "debt1")
    (root / "app.py").write_text("# TODO: wire auth\n# FIXME: broken\n", encoding="utf-8")
    graph = TaskGraph(
        [
            Task(
                id="t1",
                description="blocked",
                status="BLOCKED",
                role="ceo",
            )
        ]
    )
    graph.save(ws.tasks_path(root))
    report = scan(root)
    assert debt_path(root).is_file()
    assert report["todo_count"] >= 1
    assert report["fixme_count"] >= 1
    assert report["blocked_tasks"] == 1
    assert report["score"] in ("low", "medium", "high")
    assert report["top_hits"]
