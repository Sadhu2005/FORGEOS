from forgeos.planning.task_graph import Task, TaskGraph


def test_pick_ready_by_priority() -> None:
    graph = TaskGraph()
    graph.add(
        Task(id="b", description="later", status="READY", role="ceo", priority=50)
    )
    graph.add(
        Task(id="a", description="first", status="READY", role="ceo", priority=10)
    )
    graph.add(
        Task(id="c", description="blocked", status="BLOCKED", role="ceo", priority=1)
    )
    picked = graph.pick_ready()
    assert picked is not None
    assert picked.id == "a"


def test_invalid_status() -> None:
    try:
        Task(id="x", description="d", status="NOPE", role="ceo")
        assert False
    except ValueError:
        pass


def test_update_counts() -> None:
    graph = TaskGraph(
        [
            Task(id="1", description="d", status="COMPLETED", role="ceo"),
            Task(id="2", description="d", status="READY", role="ceo"),
            Task(id="3", description="d", status="BLOCKED", role="ceo"),
        ]
    )
    counts = graph.update_counts()
    assert counts == {"completed": 1, "pending": 1, "blocked": 1}
