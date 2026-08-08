from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws


def test_tools_list(workspace: Path, capsys) -> None:
    assert main(["tools", "list"]) == 0
    out = capsys.readouterr().out
    assert "filesystem.read" in out
    assert "git.status" in out
    assert "docker.compose_config" in out


def test_tools_exec_and_tool_demo(workspace: Path, capsys) -> None:
    assert main(["init", "tools-demo"]) == 0
    assert (
        main(
            [
                "tools",
                "exec",
                "tools-demo",
                "--role",
                "ceo",
                "--tool",
                "filesystem.tree",
                "--arg",
                "max_depth=1",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "ok=True" in out

    assert main(["run", "tools-demo", "--tool-demo"]) == 0
    demo_out = capsys.readouterr().out
    assert "terminal:" in demo_out
    assert "git.status:" in demo_out
    assert ws.state_path(ws.project_root(workspace, "tools-demo")).exists()
