"""Hierarchical planner — multi-task graphs with dependency template fallback."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from forgeos.llm.base import LLMClient
from forgeos.llm.mock import MockLLM
from forgeos.planning.scheduler import Scheduler
from forgeos.planning.task_graph import Task, TaskGraph
from forgeos.planning.templates import ceo_report_template, select_template


def default_template(
    goal: str,
    *,
    template: str | None = None,
    project_root: Path | None = None,
) -> list[Task]:
    """Seed tasks: FastAPI multi-role when matched, else Phase 4 CEO reports."""
    return select_template(goal, template=template, project_root=project_root)


def _extract_json_array(text: str) -> list[dict[str, Any]] | None:
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("tasks"), list):
        return data["tasks"]
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def tasks_from_llm_json(raw: list[dict[str, Any]], goal: str) -> list[Task] | None:
    if not raw:
        return None
    tasks: list[Task] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            return None
        tid = str(item.get("id") or f"task-{i+1:03d}")
        action = item.get("action")
        if not isinstance(action, dict) or not action.get("tool"):
            return None
        status = str(item.get("status") or ("READY" if i == 0 else "PROPOSED"))
        if status not in (
            "PROPOSED",
            "READY",
            "WAITING",
            "BLOCKED",
            "FAILED",
            "COMPLETED",
            "REJECTED",
            "CANCELLED",
            "RUNNING",
            "VERIFYING",
        ):
            status = "PROPOSED" if i else "READY"
        tasks.append(
            Task(
                id=tid,
                description=str(item.get("description") or f"Task for {goal}"),
                status=status,
                role=str(item.get("role") or "ceo"),
                priority=int(item.get("priority") or (10 * (i + 1))),
                dependencies=list(item.get("dependencies") or []),
                verification=list(item.get("verification") or ["file exists", "file is non-empty"]),
                action=dict(action),
            )
        )
    if not any(t.status == "READY" for t in tasks):
        tasks[0].status = "READY"
    return tasks


class HierarchicalPlanner:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or MockLLM()
        self.scheduler = Scheduler()

    def ensure_plan(
        self,
        goal: str,
        graph: TaskGraph,
        *,
        prompt: str | None = None,
        force: bool = False,
        template: str | None = None,
        project_root: Path | None = None,
    ) -> TaskGraph:
        if graph.tasks and not force:
            return graph
        if force:
            graph.tasks.clear()

        llm_text = self.llm.complete(
            prompt
            or (
                "Return a JSON array of tasks with id, description, status, role, "
                f"priority, dependencies, verification, action. Goal: {goal}"
            )
        )
        parsed = _extract_json_array(llm_text)
        built = tasks_from_llm_json(parsed, goal) if parsed else None
        seed = built or default_template(goal, template=template, project_root=project_root)
        for task in seed:
            if graph.get(task.id) is None:
                graph.add(task)
        return graph

    def plan(
        self,
        goal: str,
        graph: TaskGraph,
        prompt: str | None = None,
        *,
        template: str | None = None,
        project_root: Path | None = None,
    ) -> Task:
        """Back-compat: ensure plan exists, then return next scheduled task."""
        self.ensure_plan(
            goal, graph, prompt=prompt, template=template, project_root=project_root
        )
        nxt = self.scheduler.next_task(graph)
        if nxt is None:
            if not graph.tasks:
                self.ensure_plan(
                    goal,
                    graph,
                    prompt=prompt,
                    force=True,
                    template=template,
                    project_root=project_root,
                )
                nxt = self.scheduler.next_task(graph)
        if nxt is None:
            raise RuntimeError("planner: no READY task available")
        return nxt


class PlannerStub(HierarchicalPlanner):
    """Thin alias kept for Phase 1–3 imports."""


# Re-export for tests that imported the old helper name
__all__ = [
    "HierarchicalPlanner",
    "PlannerStub",
    "default_template",
    "ceo_report_template",
    "tasks_from_llm_json",
]
