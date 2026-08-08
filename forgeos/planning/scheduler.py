"""Next-task selection with dependency promotion."""

from __future__ import annotations

from forgeos.planning.task_graph import Task, TaskGraph


class Scheduler:
    def promote_ready(self, graph: TaskGraph) -> list[str]:
        return graph.promote_ready()

    def next_task(self, graph: TaskGraph) -> Task | None:
        self.promote_ready(graph)
        return graph.pick_ready()
