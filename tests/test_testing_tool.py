from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.tools.testing import TestingTool


def test_testing_run_pytest(workspace: Path) -> None:
    root = ws.create_project(workspace, "testsand")
    (root / "test_tiny.py").write_text(
        "def test_ok():\n    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )
    tool = TestingTool(root)
    result = tool.run(args=["-q", "test_tiny.py"])
    assert result.ok, result.stderr or result.stdout or result.detail
    assert result.tool == "testing.run"
