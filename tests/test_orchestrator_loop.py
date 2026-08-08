from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.core.orchestrator import Orchestrator


def test_one_cycle_writes_report(workspace: Path) -> None:
    ws.create_project(workspace, "loop")
    orch = Orchestrator(workspace, "loop", role_id="ceo")
    result = orch.run_once(goal="write hello")
    assert result.ok
    hello = ws.project_root(workspace, "loop") / ".forge" / "reports" / "hello.md"
    assert hello.exists()
    assert hello.read_text(encoding="utf-8")
    assert result.report_path is not None
    assert result.report_path.exists()
    assert orch.llm.call_count == 1
