"""Replan on task failure with capped attempts."""

from __future__ import annotations

from dataclasses import dataclass

from forgeos.planning.task_graph import Task, TaskGraph

DEFAULT_MAX_ATTEMPTS = 3


@dataclass
class ReplanResult:
    blocked: bool
    fix_task: Task | None
    message: str


class Replanner:
    def __init__(self, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> None:
        self.max_attempts = max_attempts

    def on_failure(
        self,
        graph: TaskGraph,
        task: Task,
        error: str,
        *,
        failure_class: str = "unknown",
    ) -> ReplanResult:
        task.status = "FAILED"
        task.attempts = int(task.attempts or 0) + 1
        task.last_error = f"[{failure_class}] {error}"

        if task.attempts >= self.max_attempts:
            task.status = "BLOCKED"
            return ReplanResult(
                blocked=True,
                fix_task=None,
                message=f"blocked after {task.attempts} attempts [{failure_class}]: {error}",
            )

        n = task.attempts
        fix_id = f"{task.id}-fix-{n}"
        if graph.get(fix_id) is not None:
            fix_id = f"{task.id}-fix-{n}-b"
        fix = Task(
            id=fix_id,
            description=f"Fix [{failure_class}] after failure of {task.id}: {error[:120]}",
            status="READY",
            role=task.role or "ceo",
            priority=max(1, int(task.priority) - 1),
            verification=["file exists", "file is non-empty"],
            action={
                "tool": "filesystem.write",
                "path": f".forge/reports/fix-{task.id}-{n}.md",
                "content": (
                    f"# FORGEOS fix report\n\nFailed task: {task.id}\n"
                    f"Failure class: {failure_class}\n"
                    f"Attempt: {n}\nError: {error}\n\n"
                    "Status: fix artifact recorded.\n"
                ),
            },
            attempts=0,
        )
        graph.add(fix)
        return ReplanResult(
            blocked=False,
            fix_task=fix,
            message=f"replan [{failure_class}]: added {fix_id}",
        )
