from pathlib import Path

import pytest

from forgeos.core import world_state as ws
from forgeos.tools.filesystem import FilesystemTool, PathNotAllowedError


def test_allow_forge_write(workspace: Path) -> None:
    root = ws.create_project(workspace, "fs")
    tool = FilesystemTool(root, [".forge/**"])
    path = tool.write(".forge/reports/x.md", "hi")
    assert path.exists()
    assert tool.read(".forge/reports/x.md") == "hi"


def test_deny_outside_glob(workspace: Path) -> None:
    root = ws.create_project(workspace, "fs2")
    tool = FilesystemTool(root, [".forge/**"])
    with pytest.raises(PathNotAllowedError):
        tool.write("secret.txt", "nope")


def test_deny_escape(workspace: Path) -> None:
    root = ws.create_project(workspace, "fs3")
    tool = FilesystemTool(root, ["**"])
    with pytest.raises(PathNotAllowedError):
        tool.write("../outside.txt", "nope")
