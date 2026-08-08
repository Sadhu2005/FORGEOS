"""Dashboard mutations: approvals, intel probes, checkpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forgeos.core import world_state as ws
from forgeos.intelligence.debt import scan as debt_scan
from forgeos.intelligence.health import probe as health_probe
from forgeos.planning.task_graph import TaskGraph
from forgeos.safety.approval import ApprovalStore
from forgeos.safety.audit import AuditLog
from forgeos.tools.git import GitTool


def _unblock_task(project: Path, task_id: str) -> None:
    graph = TaskGraph.load(ws.tasks_path(project))
    task = graph.get(task_id)
    if task is not None and task.status == "BLOCKED":
        task.status = "READY"
        task.last_error = ""
        graph.save(ws.tasks_path(project))


def approve(project: Path, approval_id: str) -> dict[str, Any]:
    ticket = ApprovalStore(project).approve(approval_id)
    _unblock_task(project, str(ticket.get("task_id") or ""))
    AuditLog(project).append(
        "approval",
        f"approved {ticket['id']}",
        task_id=str(ticket.get("task_id") or ""),
        payload={"approval_id": ticket["id"], "status": "approved", "via": "dashboard"},
    )
    return ticket


def reject(project: Path, approval_id: str) -> dict[str, Any]:
    ticket = ApprovalStore(project).reject(approval_id)
    AuditLog(project).append(
        "approval",
        f"rejected {ticket['id']}",
        task_id=str(ticket.get("task_id") or ""),
        payload={"approval_id": ticket["id"], "status": "rejected", "via": "dashboard"},
    )
    return ticket


def run_health(project: Path) -> dict[str, Any]:
    return health_probe(project)


def run_debt(project: Path) -> dict[str, Any]:
    return debt_scan(project)


def create_checkpoint(project: Path, message: str = "") -> dict[str, Any]:
    result = GitTool(project).checkpoint(message=message or "dashboard checkpoint")
    AuditLog(project).append(
        "checkpoint",
        result.detail,
        payload={**(result.data or {}), "via": "dashboard"},
    )
    return dict(result.data or {"detail": result.detail})
