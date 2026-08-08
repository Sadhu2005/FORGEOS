from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.core.orchestrator import Orchestrator


def test_one_cycle_writes_report(workspace: Path) -> None:
    ws.create_project(workspace, "loop")
    orch = Orchestrator(workspace, "loop", role_id="ceo")
    batch = orch.run_steps(goal="write hello", steps=2)
    assert batch.ok
    hello = ws.project_root(workspace, "loop") / ".forge" / "reports" / "hello.md"
    assert hello.exists()
    assert hello.read_text(encoding="utf-8")
    assert batch.cycles[-1].report_path is not None
    assert batch.cycles[-1].report_path.exists()
    assert orch.llm.call_count == 1
