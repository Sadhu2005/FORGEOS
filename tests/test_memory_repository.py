from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.memory.repository import Repository
from forgeos.planning.task_graph import Task, TaskGraph


def test_sync_from_yaml_mirrors_tasks(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "mem-repo")
    graph = TaskGraph(
        [
            Task(
                id="task-001",
                description="write report",
                status="READY",
                role="ceo",
                priority=10,
                dependencies=[],
                verification=["exists"],
                action={"tool": "filesystem.write", "path": ".forge/reports/a.md", "content": "x"},
            )
        ]
    )
    graph.save(ws.tasks_path(root))
    repo = Repository(root)
    repo.sync_from_yaml()
    tasks = repo.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["id"] == "task-001"
    assert tasks[0]["status"] == "READY"
    counts = repo.counts()
    assert counts["tasks"] == 1
    assert counts["project_meta"] == 1


def test_decisions_and_events(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "mem-repo2")
    repo = Repository(root)
    did = repo.add_decision(
        problem="ModuleNotFoundError",
        options=["retry", "block"],
        chosen="replan",
        confidence="HIGH",
        reason="missing dep",
        evidence=["detail"],
    )
    eid = repo.add_event(kind="cycle", task_id="task-001", payload={"ok": False})
    assert did.startswith("dec-")
    assert eid.startswith("evt-")
    decisions = repo.list_decisions()
    assert len(decisions) == 1
    assert decisions[0]["chosen"] == "replan"
    events = repo.recent_events()
    assert len(events) == 1
    assert events[0]["kind"] == "cycle"
