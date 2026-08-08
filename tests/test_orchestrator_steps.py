from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.core.orchestrator import Orchestrator


def test_two_steps_complete_template(workspace: Path) -> None:
    ws.create_project(workspace, "steps")
    orch = Orchestrator(workspace, "steps", role_id="ceo")
    batch = orch.run_steps(goal="write hello", steps=2)
    assert batch.ok
    root = ws.project_root(workspace, "steps")
    assert (root / ".forge" / "reports" / "phase.md").exists()
    assert (root / ".forge" / "reports" / "hello.md").exists()
    assert orch.llm.call_count == 1


def test_task_role_used(workspace: Path) -> None:
    ws.create_project(workspace, "roleproj")
    orch = Orchestrator(workspace, "roleproj", role_id="backend")
    # plan template uses ceo roles on tasks
    result = orch.run_once(goal="write hello")
    assert result.ok
    assert result.task_id == "task-001"
