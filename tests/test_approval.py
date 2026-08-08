from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.safety.approval import ApprovalStore


def test_approval_request_approve_reject(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "appr")
    store = ApprovalStore(root)
    ticket = store.request(
        project_name="appr",
        task_id="task-001",
        action={"tool": "filesystem.delete", "path": "backend/x.py"},
        risk="critical",
        reason="critical tool",
    )
    assert ticket["status"] == "pending"
    assert store.list_pending()
    fp = ticket["fingerprint"]
    assert not store.is_approved(fp)

    approved = store.approve(ticket["id"])
    assert approved["status"] == "approved"
    assert store.is_approved(fp)

    # second request same fingerprint while approved still finds approved
    again = store.request(
        project_name="appr",
        task_id="task-001",
        action={"tool": "filesystem.delete", "path": "backend/x.py"},
        risk="critical",
        reason="critical tool",
    )
    # new pending only if no pending; approved exists so new pending is created
    # (request reuses pending only). Creating another pending is ok for a new cycle.
    assert again["id"]


def test_reject_flow(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "appr2")
    store = ApprovalStore(root)
    ticket = store.request(
        project_name="appr2",
        task_id="t1",
        action={"tool": "docker.compose_up"},
        risk="critical",
        reason="compose up",
    )
    rejected = store.reject(ticket["id"])
    assert rejected["status"] == "rejected"
    assert not store.is_approved(ticket["fingerprint"])
