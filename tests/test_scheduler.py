from forgeos.planning.scheduler import Scheduler
from forgeos.planning.task_graph import Task, TaskGraph


def test_promote_and_next_by_priority() -> None:
    graph = TaskGraph(
        [
            Task(
                id="a",
                description="root",
                status="COMPLETED",
                role="ceo",
                priority=10,
            ),
            Task(
                id="b",
                description="child",
                status="PROPOSED",
                role="ceo",
                priority=5,
                dependencies=["a"],
            ),
            Task(
                id="c",
                description="other ready",
                status="READY",
                role="ceo",
                priority=50,
            ),
        ]
    )
    sched = Scheduler()
    nxt = sched.next_task(graph)
    assert nxt is not None
    assert nxt.id == "b"
    assert graph.get("b") is not None
    assert graph.get("b").status == "READY"


def test_deps_block_promotion() -> None:
    graph = TaskGraph(
        [
            Task(id="a", description="root", status="READY", role="ceo", priority=1),
            Task(
                id="b",
                description="child",
                status="PROPOSED",
                role="ceo",
                priority=1,
                dependencies=["a"],
            ),
        ]
    )
    assert Scheduler().next_task(graph).id == "a"
    assert graph.get("b").status == "PROPOSED"
