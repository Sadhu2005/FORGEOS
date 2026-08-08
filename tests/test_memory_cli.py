from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.memory.database import memory_path


def test_memory_cli_sync_status_decisions(workspace: Path, capsys) -> None:
    assert main(["init", "mem-cli"]) == 0
    assert main(["plan", "mem-cli", "--goal", "memory demo"]) == 0
    assert main(["memory", "sync", "mem-cli"]) == 0
    out = capsys.readouterr().out
    assert "synced:" in out

    assert main(["memory", "status", "mem-cli"]) == 0
    status = capsys.readouterr().out
    assert "db:" in status
    assert "tasks:" in status
    root = ws.project_root(workspace, "mem-cli")
    assert memory_path(root).is_file()

    assert main(["run", "mem-cli", "--goal", "memory demo", "--steps", "1"]) == 0
    capsys.readouterr()
    assert main(["memory", "decisions", "mem-cli"]) == 0
    # successful run may have no decisions; command still succeeds
    assert main(["memory", "status", "mem-cli"]) == 0
    status2 = capsys.readouterr().out
    assert "events:" in status2
