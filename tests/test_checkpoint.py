from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.tools.git import GitTool


def test_checkpoint_create_and_list(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "ckpt")
    git = GitTool(root)
    # Create an initial commit so tagging works.
    (root / "README.md").write_text("hi\n", encoding="utf-8")
    commit = git.commit("init")
    assert commit.ok, commit.stderr or commit.detail
    result = git.checkpoint(message="before critical")
    assert result.ok
    assert result.data
    assert result.data.get("sha")
    entries = git.list_checkpoints()
    assert len(entries) == 1
    assert entries[0]["message"] == "before critical"
