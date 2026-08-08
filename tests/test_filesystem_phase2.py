from pathlib import Path

import pytest

from forgeos.core import world_state as ws
from forgeos.tools.filesystem import FilesystemTool, PathNotAllowedError


def test_edit_search_tree_delete(workspace: Path) -> None:
    root = ws.create_project(workspace, "fs2")
    tool = FilesystemTool(root, [".forge/**"])
    tool.write(".forge/reports/a.md", "hello world")
    tool.edit(".forge/reports/a.md", "world", "forgeos")
    assert tool.read(".forge/reports/a.md") == "hello forgeos"

    hits = tool.search("forgeos", root=".forge")
    assert any(h["path"].endswith("a.md") for h in hits)

    tree = tool.tree(root=".forge", max_depth=2)
    assert any("a.md" in line for line in tree)

    deleted = tool.delete(".forge/reports/a.md")
    assert not deleted.exists()


def test_delete_denied_outside_glob(workspace: Path) -> None:
    root = ws.create_project(workspace, "fs2b")
    (root / "secret.txt").write_text("x", encoding="utf-8")
    tool = FilesystemTool(root, [".forge/**"])
    with pytest.raises(PathNotAllowedError):
        tool.delete("secret.txt")


def test_edit_escape_denied(workspace: Path) -> None:
    root = ws.create_project(workspace, "fs2c")
    tool = FilesystemTool(root, ["**"])
    with pytest.raises(PathNotAllowedError):
        tool.edit("../outside.txt", "", "nope")
