from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws


def test_cli_init_run_status(workspace: Path, capsys) -> None:
    assert main(["init", "cli-demo"]) == 0
    root = ws.project_root(workspace, "cli-demo")
    assert ws.state_path(root).exists()

    assert main(["run", "cli-demo", "--goal", "cli goal"]) == 0
    out = capsys.readouterr().out
    assert "cycle completed" in out or "COMPLETED" in out or "task:" in out

    assert main(["status", "cli-demo"]) == 0
    status_out = capsys.readouterr().out
    assert "cli-demo" in status_out
    assert "phase:" in status_out
