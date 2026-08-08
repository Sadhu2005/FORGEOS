"""Task graph with dependency helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

STATUSES = (
    "PROPOSED",
    "READY",
    "RUNNING",
    "WAITING",
    "BLOCKED",
    "FAILED",
    "VERIFYING",
    "COMPLETED",
    "REJECTED",
    "CANCELLED",
)


@dataclass
class Task:
    id: str
    description: str
    status: str
    role: str
    priority: int = 100
    dependencies: list[str] = field(default_factory=list)
    risk: str = "low"
    verification: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    action: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    last_error: str = ""

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"invalid status: {self.status}")


_TASK_FIELD_NAMES = {f.name for f in fields(Task)}


class TaskGraph:
    def __init__(self, tasks: list[Task] | None = None) -> None:
        self.tasks: list[Task] = list(tasks or [])

    def add(self, task: Task) -> None:
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"duplicate task id: {task.id}")
        self.tasks.append(task)

    def get(self, task_id: str) -> Task | None:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def deps_completed(self, task: Task) -> bool:
        for dep_id in task.dependencies:
            dep = self.get(dep_id)
            if dep is None or dep.status != "COMPLETED":
                return False
        return True

    def promote_ready(self) -> list[str]:
        """Promote PROPOSED tasks to READY when all dependencies are COMPLETED."""
        promoted: list[str] = []
        for task in self.tasks:
            if task.status != "PROPOSED":
                continue
            if self.deps_completed(task):
                task.status = "READY"
                promoted.append(task.id)
        return promoted

    def pick_ready(self) -> Task | None:
        ready = [t for t in self.tasks if t.status == "READY"]
        if not ready:
            return None
        ready.sort(key=lambda t: (t.priority, t.id))
        return ready[0]

    def has_incomplete(self) -> bool:
        return any(
            t.status
            in ("PROPOSED", "READY", "WAITING", "RUNNING", "VERIFYING", "FAILED")
            for t in self.tasks
        )

    def update_counts(self) -> dict[str, int]:
        completed = sum(1 for t in self.tasks if t.status == "COMPLETED")
        blocked = sum(1 for t in self.tasks if t.status == "BLOCKED")
        pending = sum(
            1
            for t in self.tasks
            if t.status in ("PROPOSED", "READY", "WAITING", "RUNNING", "VERIFYING")
        )
        return {"completed": completed, "pending": pending, "blocked": blocked}

    def to_list(self) -> list[dict[str, Any]]:
        return [asdict(t) for t in self.tasks]

    @classmethod
    def from_list(cls, raw: list[dict[str, Any]]) -> TaskGraph:
        tasks: list[Task] = []
        for item in raw:
            filtered = {k: v for k, v in item.items() if k in _TASK_FIELD_NAMES}
            tasks.append(Task(**filtered))
        return cls(tasks)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump({"tasks": self.to_list()}, sort_keys=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> TaskGraph:
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_list(data.get("tasks") or [])
