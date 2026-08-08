"""Tool registry — name to handler dispatch."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from forgeos.roles.loader import RolePolicy
from forgeos.tools.base import ToolResult
from forgeos.tools.docker import DockerTool
from forgeos.tools.filesystem import FilesystemTool
from forgeos.tools.git import GitTool
from forgeos.tools.terminal import TerminalTool
from forgeos.tools.testing import TestingTool

Handler = Callable[[dict[str, Any]], ToolResult]


class ToolRegistry:
    def __init__(self, project_root: Path, role: RolePolicy) -> None:
        self.project_root = project_root.resolve()
        self.role = role
        self.fs = FilesystemTool(self.project_root, role.writes)
        self.terminal = TerminalTool(self.project_root)
        self.git = GitTool(self.project_root)
        self.testing = TestingTool(self.project_root)
        self.docker = DockerTool(self.project_root)
        self._handlers: dict[str, Handler] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("filesystem.read", self._fs_read)
        self.register("filesystem.write", self._fs_write)
        self.register("filesystem.edit", self._fs_edit)
        self.register("filesystem.search", self._fs_search)
        self.register("filesystem.tree", self._fs_tree)
        self.register("filesystem.delete", self._fs_delete)
        self.register("terminal.execute", self._terminal_execute)
        self.register("git.status", self._git_status)
        self.register("git.diff", self._git_diff)
        self.register("git.branch", self._git_branch)
        self.register("git.commit", self._git_commit)
        self.register("git.checkpoint", self._git_checkpoint)
        self.register("testing.run", self._testing_run)
        self.register("docker.compose_config", self._docker_compose_config)
        self.register("docker.compose_up", self._docker_compose_up)

    def register(self, name: str, handler: Handler) -> None:
        self._handlers[name] = handler

    def list_tools(self) -> list[str]:
        return sorted(self._handlers)

    def dispatch(self, action: dict[str, Any]) -> ToolResult:
        tool = action.get("tool")
        if not tool:
            return ToolResult(False, "", "missing action.tool")
        if tool not in self.role.allowed_tools:
            return ToolResult(
                False,
                str(tool),
                f"tool not allowed by role {self.role.id}: {tool}",
            )
        handler = self._handlers.get(str(tool))
        if handler is None:
            return ToolResult(False, str(tool), f"unknown tool: {tool}")
        return handler(action)

    def _fs_read(self, action: dict[str, Any]) -> ToolResult:
        path = action.get("path")
        if not path:
            return ToolResult(False, "filesystem.read", "missing action.path")
        text = self.fs.read(str(path))
        return ToolResult(True, "filesystem.read", f"read {len(text)} chars", path=str(path), data={"content": text})

    def _fs_write(self, action: dict[str, Any]) -> ToolResult:
        path = action.get("path")
        if not path:
            return ToolResult(False, "filesystem.write", "missing action.path")
        written = self.fs.write(str(path), str(action.get("content", "")))
        return ToolResult(True, "filesystem.write", "written", path=str(written))

    def _fs_edit(self, action: dict[str, Any]) -> ToolResult:
        path = action.get("path")
        if not path:
            return ToolResult(False, "filesystem.edit", "missing action.path")
        written = self.fs.edit(str(path), str(action.get("old", "")), str(action.get("new", "")))
        return ToolResult(True, "filesystem.edit", "edited", path=str(written))

    def _fs_search(self, action: dict[str, Any]) -> ToolResult:
        query = action.get("query")
        if not query:
            return ToolResult(False, "filesystem.search", "missing action.query")
        hits = self.fs.search(str(query), root=str(action.get("root", ".")), max_hits=int(action.get("max_hits", 50)))
        return ToolResult(True, "filesystem.search", f"{len(hits)} hits", data={"hits": hits})

    def _fs_tree(self, action: dict[str, Any]) -> ToolResult:
        lines = self.fs.tree(root=str(action.get("root", ".")), max_depth=int(action.get("max_depth", 3)))
        return ToolResult(True, "filesystem.tree", f"{len(lines)} entries", data={"tree": lines})

    def _fs_delete(self, action: dict[str, Any]) -> ToolResult:
        path = action.get("path")
        if not path:
            return ToolResult(False, "filesystem.delete", "missing action.path")
        deleted = self.fs.delete(str(path))
        return ToolResult(True, "filesystem.delete", "deleted", path=str(deleted))

    def _terminal_execute(self, action: dict[str, Any]) -> ToolResult:
        command = action.get("command")
        if not command:
            return ToolResult(False, "terminal.execute", "missing action.command")
        timeout = action.get("timeout_s")
        return self.terminal.execute(str(command), timeout_s=float(timeout) if timeout is not None else None)

    def _git_status(self, action: dict[str, Any]) -> ToolResult:
        return self.git.status()

    def _git_diff(self, action: dict[str, Any]) -> ToolResult:
        return self.git.diff(staged=bool(action.get("staged", False)))

    def _git_branch(self, action: dict[str, Any]) -> ToolResult:
        return self.git.branch(name=action.get("name"), create=bool(action.get("create", False)))

    def _git_commit(self, action: dict[str, Any]) -> ToolResult:
        message = action.get("message")
        if not message:
            return ToolResult(False, "git.commit", "missing action.message")
        return self.git.commit(str(message), add_all=bool(action.get("add_all", True)))

    def _git_checkpoint(self, action: dict[str, Any]) -> ToolResult:
        return self.git.checkpoint(message=str(action.get("message", "")))

    def _testing_run(self, action: dict[str, Any]) -> ToolResult:
        args = action.get("args")
        if args is not None and not isinstance(args, list):
            return ToolResult(False, "testing.run", "action.args must be a list")
        return self.testing.run(args=args)

    def _docker_compose_config(self, action: dict[str, Any]) -> ToolResult:
        compose_file = str(action.get("compose_file", "docker/docker-compose.yml"))
        return self.docker.compose_config(compose_file=compose_file)

    def _docker_compose_up(self, action: dict[str, Any]) -> ToolResult:
        compose_file = str(action.get("compose_file", "docker/docker-compose.yml"))
        return self.docker.compose_up(compose_file=compose_file)


def default_tool_ids() -> list[str]:
    """Tool ids registered by ToolRegistry defaults (no project needed)."""
    return sorted(
        [
            "filesystem.read",
            "filesystem.write",
            "filesystem.edit",
            "filesystem.search",
            "filesystem.tree",
            "filesystem.delete",
            "terminal.execute",
            "git.status",
            "git.diff",
            "git.branch",
            "git.commit",
            "git.checkpoint",
            "testing.run",
            "docker.compose_config",
            "docker.compose_up",
        ]
    )
