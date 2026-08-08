from pathlib import Path

import pytest

from forgeos.core import world_state as ws
from forgeos.tools.terminal import TerminalDeniedError, TerminalTool


def test_terminal_echo(workspace: Path) -> None:
    root = ws.create_project(workspace, "term")
    tool = TerminalTool(root)
    result = tool.execute("echo forgeos-ok")
    assert result.ok
    assert "forgeos-ok" in result.stdout


def test_terminal_deny_list(workspace: Path) -> None:
    root = ws.create_project(workspace, "term2")
    tool = TerminalTool(root)
    with pytest.raises(TerminalDeniedError):
        tool.execute("rm -rf /")
    with pytest.raises(TerminalDeniedError):
        tool.execute("git reset --hard")
    with pytest.raises(TerminalDeniedError):
        tool.execute("git push --force origin main")


def test_terminal_cwd_is_project(workspace: Path) -> None:
    root = ws.create_project(workspace, "term3")
    tool = TerminalTool(root)
    result = tool.execute("echo %CD%" if __import__("os").name == "nt" else "pwd")
    assert result.ok
    out = (result.stdout + result.stderr).lower().replace("/", "\\")
    assert str(root.resolve()).lower().replace("/", "\\") in out
