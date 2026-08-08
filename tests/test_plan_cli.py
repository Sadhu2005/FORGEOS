from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws


def test_plan_tasks_run_steps(workspace: Path, capsys) -> None:
    assert main(["init", "plan-demo"]) == 0
    assert main(["plan", "plan-demo", "--goal", "ship phase4", "--llm", "mock"]) == 0
    out = capsys.readouterr().out
    assert "task-001" in out
    assert "task-002" in out

    assert main(["tasks", "list", "plan-demo"]) == 0
    listed = capsys.readouterr().out
    assert "task-001" in listed
    assert "READY" in listed or "PROPOSED" in listed

    assert main(["run", "plan-demo", "--steps", "2", "--goal", "ship phase4"]) == 0
    root = ws.project_root(workspace, "plan-demo")
    assert (root / ".forge" / "reports" / "phase.md").exists()
    assert (root / ".forge" / "reports" / "hello.md").exists()
