from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.core.orchestrator import Orchestrator
from forgeos.planning.task_graph import Task, TaskGraph
from forgeos.safety.approval import ApprovalStore
from forgeos.safety.audit import audit_path


def test_critical_block_approve_resume(workspace: Path, capsys) -> None:
    assert main(["init", "safe-demo"]) == 0
    root = ws.project_root(workspace, "safe-demo")
    # Seed a critical delete task for backend (has filesystem.delete).
    (root / "backend").mkdir(parents=True, exist_ok=True)
    target = root / "backend" / "temp.txt"
    target.write_text("x", encoding="utf-8")
    graph = TaskGraph(
        [
            Task(
                id="task-del",
                description="delete temp",
                status="READY",
                role="backend",
                risk="low",
                verification=[],
                action={"tool": "filesystem.delete", "path": "backend/temp.txt"},
            )
        ]
    )
    graph.save(ws.tasks_path(root))

    orch = Orchestrator(workspace, "safe-demo")
    result = orch.run_once(goal="delete")
    assert not result.ok
    assert "blocked for human review" in result.message
    pending = ApprovalStore(root).list_pending()
    assert len(pending) == 1
    aid = pending[0]["id"]

    assert main(["safety", "pending", "safe-demo"]) == 0
    out = capsys.readouterr().out
    assert aid in out

    assert main(["safety", "approve", "safe-demo", "--id", aid]) == 0
    graph2 = TaskGraph.load(ws.tasks_path(root))
    assert graph2.get("task-del").status == "READY"

    result2 = orch.run_once(goal="delete")
    assert result2.ok
    assert not target.exists()

    assert main(["safety", "audit", "safe-demo"]) == 0
    audit_out = capsys.readouterr().out
    assert "approval" in audit_out
    assert audit_path(root).is_file()


def test_checkpoint_cli(workspace: Path, capsys) -> None:
    assert main(["init", "ckpt-demo"]) == 0
    root = ws.project_root(workspace, "ckpt-demo")
    (root / "f.txt").write_text("a", encoding="utf-8")
    from forgeos.tools.git import GitTool

    GitTool(root).commit("init")
    assert main(["checkpoint", "create", "ckpt-demo", "--message", "snap"]) == 0
    assert main(["checkpoint", "list", "ckpt-demo"]) == 0
    out = capsys.readouterr().out
    assert "snap" in out or "forgeos-ckpt-" in out
