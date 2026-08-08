from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.dashboard import actions
from forgeos.planning.task_graph import Task, TaskGraph
from forgeos.safety.approval import ApprovalStore
from forgeos.safety.audit import audit_path


def test_approve_unblocks_and_audits(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "act1")
    graph = TaskGraph(
        [
            Task(
                id="task-del",
                description="delete",
                status="BLOCKED",
                role="backend",
                action={"tool": "filesystem.delete", "path": "backend/x.txt"},
            )
        ]
    )
    graph.save(ws.tasks_path(root))
    ticket = ApprovalStore(root).request(
        project_name="act1",
        task_id="task-del",
        action={"tool": "filesystem.delete", "path": "backend/x.txt"},
        risk="critical",
        reason="critical tool",
    )
    actions.approve(root, ticket["id"])
    graph2 = TaskGraph.load(ws.tasks_path(root))
    assert graph2.get("task-del").status == "READY"
    assert audit_path(root).is_file()


def test_health_debt_checkpoint_actions(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "act2")
    (root / "app.py").write_text("# TODO: x\n", encoding="utf-8")
    health = actions.run_health(root)
    assert "tests" in health
    debt = actions.run_debt(root)
    assert debt["todo_count"] >= 1
    ckpt = actions.create_checkpoint(root, message="snap")
    assert "id" in ckpt or "detail" in ckpt or ckpt.get("message")
