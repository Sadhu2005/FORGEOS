from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.llm.context_manager import ContextManager
from forgeos.memory.repository import Repository
from forgeos.memory.summarizer import Summarizer
from forgeos.planning.task_graph import Task, TaskGraph


def test_summarizer_counts_and_decision(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "mem-sum")
    graph = TaskGraph(
        [
            Task(
                id="task-001",
                description="done work",
                status="COMPLETED",
                role="ceo",
            ),
            Task(
                id="task-002",
                description="pending work",
                status="READY",
                role="ceo",
            ),
        ]
    )
    graph.save(ws.tasks_path(root))
    repo = Repository(root)
    repo.sync_from_yaml()
    repo.add_decision(
        problem="fail",
        options=["retry", "block"],
        chosen="replan",
        confidence="MEDIUM",
        reason="retry",
    )
    text = Summarizer(root).summarize(limit=5)
    assert "## Memory" in text
    assert "completed=1" in text
    assert "pending=1" in text
    assert "Last decision" in text
    assert "replan" in text


def test_context_includes_memory(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "mem-ctx")
    graph = TaskGraph(
        [Task(id="t1", description="x", status="READY", role="ceo")]
    )
    graph.save(ws.tasks_path(root))
    Repository(root).sync_from_yaml()
    prompt = ContextManager(project_root=root).build(
        goal="g",
        role_id="ceo",
        allowed_tools=["filesystem.write"],
    )
    assert "## Memory" in prompt
    assert "Tasks:" in prompt
