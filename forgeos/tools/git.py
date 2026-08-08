"""Git tools scoped to a project sandbox."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from forgeos.core import world_state as ws
from forgeos.tools.base import ToolResult

CHECKPOINTS_FILE = "checkpoints.yaml"


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

    def current_branch(self) -> str:
        self.ensure_repo()
        result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        if result.ok and result.stdout.strip():
            name = result.stdout.strip()
            if name != "HEAD":
                return name
        return "main"

    def head_sha(self) -> str:
        self.ensure_repo()
        result = self._run(["rev-parse", "HEAD"])
        if result.ok:
            return result.stdout.strip()
        return ""

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

    def checkpoints_path(self) -> Path:
        return ws.forge_dir(self.project_root) / CHECKPOINTS_FILE

    def list_checkpoints(self) -> list[dict[str, Any]]:
        path = self.checkpoints_path()
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return list(data.get("checkpoints") or [])

    def checkpoint(self, message: str = "") -> ToolResult:
        """Record HEAD in .forge/checkpoints.yaml and tag forgeos-ckpt-<utc> when possible."""
        self.ensure_repo()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        tag = f"forgeos-ckpt-{stamp}"
        sha = self.head_sha()
        tag_created = False
        if sha:
            tagged = self._run(["tag", tag])
            tag_created = tagged.ok
        entry = {
            "id": tag,
            "sha": sha,
            "message": message or f"checkpoint {stamp}",
            "tag": tag if tag_created else "",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        path = self.checkpoints_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.list_checkpoints()
        existing.append(entry)
        path.write_text(
            yaml.safe_dump({"checkpoints": existing}, sort_keys=False),
            encoding="utf-8",
        )
        detail = f"sha={sha or '(none)'} tag={tag if tag_created else '(skipped)'}"
        return ToolResult(
            True,
            "git.checkpoint",
            detail,
            path=str(path),
            data=entry,
        )
