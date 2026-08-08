"""Git tools scoped to a project sandbox."""

from __future__ import annotations

import subprocess
from pathlib import Path

from forgeos.tools.base import ToolResult


class GitDangerousError(PermissionError):
    pass


class GitTool:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def _run(self, args: list[str]) -> ToolResult:
        if "push" in args and ("--force" in args or "-f" in args):
            raise GitDangerousError("git force-push is refused")
        if len(args) >= 2 and args[0] == "reset" and "--hard" in args:
            raise GitDangerousError("git reset --hard is refused")
        completed = subprocess.run(
            ["git", *args],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )
        return ToolResult(
            ok=completed.returncode == 0,
            tool=f"git.{args[0] if args else 'unknown'}",
            detail=f"exit={completed.returncode}",
            exit_code=completed.returncode,
            stdout=(completed.stdout or "")[-8000:],
            stderr=(completed.stderr or "")[-4000:],
        )

    def ensure_repo(self) -> None:
        git_dir = self.project_root / ".git"
        if git_dir.exists():
            return
        init = self._run(["init"])
        if not init.ok:
            raise RuntimeError(f"git init failed: {init.stderr or init.detail}")

    def status(self) -> ToolResult:
        self.ensure_repo()
        result = self._run(["status", "--short", "--branch"])
        result.tool = "git.status"
        return result

    def diff(self, staged: bool = False) -> ToolResult:
        self.ensure_repo()
        args = ["diff", "--staged"] if staged else ["diff"]
        result = self._run(args)
        result.tool = "git.diff"
        return result

    def branch(self, name: str | None = None, create: bool = False) -> ToolResult:
        self.ensure_repo()
        if name and create:
            result = self._run(["checkout", "-b", name])
        elif name:
            result = self._run(["checkout", name])
        else:
            result = self._run(["branch", "--list"])
        result.tool = "git.branch"
        return result

    def commit(self, message: str, add_all: bool = True) -> ToolResult:
        if not message.strip():
            return ToolResult(False, "git.commit", "empty commit message")
        self.ensure_repo()
        if add_all:
            add = self._run(["add", "-A"])
            if not add.ok:
                add.tool = "git.commit"
                return add
        # Ensure identity for sandboxes without global git config
        subprocess.run(
            ["git", "config", "user.email", "forgeos@local"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "FORGEOS"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )
        result = self._run(["commit", "-m", message])
        result.tool = "git.commit"
        return result
