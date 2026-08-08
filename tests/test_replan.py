from forgeos.planning.replan import Replanner
from forgeos.planning.task_graph import Task, TaskGraph


def test_replan_adds_fix_then_blocks() -> None:
    graph = TaskGraph()
    task = Task(
        id="task-001",
        description="x",
        status="RUNNING",
        role="ceo",
        priority=10,
        action={"tool": "filesystem.write", "path": ".forge/reports/x.md", "content": "x"},
    )
    graph.add(task)
    replanner = Replanner(max_attempts=2)

    r1 = replanner.on_failure(graph, task, "boom")
    assert not r1.blocked
    assert r1.fix_task is not None
    assert graph.get(r1.fix_task.id) is not None
    assert task.attempts == 1
    assert task.status == "FAILED"

    r2 = replanner.on_failure(graph, task, "boom again")
    assert r2.blocked
    assert task.status == "BLOCKED"
    assert task.attempts == 2
