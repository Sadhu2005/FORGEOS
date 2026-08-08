from pathlib import Path

import pytest

from forgeos.core import world_state as ws
from forgeos.tools.git import GitDangerousError, GitTool


def test_git_status_diff_branch_commit(workspace: Path) -> None:
    root = ws.create_project(workspace, "gitproj")
    tool = GitTool(root)
    status = tool.status()
    assert status.ok
    assert status.tool == "git.status"

    (root / "note.txt").write_text("hi", encoding="utf-8")
    diff = tool.diff()
    assert diff.ok

    branch = tool.branch()
    assert branch.ok

    created = tool.branch(name="feature/demo", create=True)
    assert created.ok

    commit = tool.commit("test: phase2 commit")
    assert commit.ok, commit.stderr or commit.detail


def test_git_refuse_force_and_hard_reset(workspace: Path) -> None:
    root = ws.create_project(workspace, "gitdeny")
    tool = GitTool(root)
    tool.ensure_repo()
    with pytest.raises(GitDangerousError):
        tool._run(["push", "--force", "origin", "main"])
    with pytest.raises(GitDangerousError):
        tool._run(["reset", "--hard", "HEAD"])
