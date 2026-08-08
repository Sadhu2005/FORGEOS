"""Phase 1 planner stub — one write-file READY task via MockLLM."""

from __future__ import annotations

from forgeos.llm.mock import MockLLM
from forgeos.planning.task_graph import Task, TaskGraph


class PlannerStub:
    def __init__(self, llm: MockLLM | None = None) -> None:
        self.llm = llm or MockLLM()

    def plan(self, goal: str, graph: TaskGraph) -> Task:
        """Ask MockLLM for a plan and add a single READY filesystem.write task."""
        _ = self.llm.complete(f"plan:{goal}")
        task = Task(
            id="task-001",
            description=f"Write report for goal: {goal}",
            status="READY",
            role="ceo",
            priority=10,
            verification=[
                "file exists",
                "file is non-empty",
            ],
            action={
                "tool": "filesystem.write",
                "path": ".forge/reports/hello.md",
                "content": (
                    f"# FORGEOS Phase 1 stub report\n\nGoal: {goal}\n\n"
                    "Status: cycle completed.\n"
                ),
            },
        )
        if graph.get(task.id) is None:
            graph.add(task)
        else:
            existing = graph.get(task.id)
            assert existing is not None
            existing.status = "READY"
            existing.action = task.action
            existing.verification = task.verification
            existing.description = task.description
        return task
