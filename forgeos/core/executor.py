"""Execute validated tool actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forgeos.roles.loader import RolePolicy
from forgeos.tools.filesystem import FilesystemTool


@dataclass
class ExecResult:
    ok: bool
    tool: str
    detail: str
    path: str | None = None


class Executor:
    def __init__(self, fs: FilesystemTool, role: RolePolicy) -> None:
        self.fs = fs
        self.role = role

    def execute(self, action: dict[str, Any]) -> ExecResult:
        tool = action.get("tool")
        if not tool:
            return ExecResult(False, "", "missing action.tool")
        if tool not in self.role.allowed_tools:
            return ExecResult(
                False,
                tool,
                f"tool not allowed by role {self.role.id}: {tool}",
            )
        if tool == "filesystem.write":
            path = action.get("path")
            content = action.get("content", "")
            if not path:
                return ExecResult(False, tool, "missing action.path")
            written = self.fs.write(str(path), str(content))
            return ExecResult(True, tool, "written", path=str(written))
        if tool == "filesystem.read":
            path = action.get("path")
            if not path:
                return ExecResult(False, tool, "missing action.path")
            text = self.fs.read(str(path))
            return ExecResult(True, tool, f"read {len(text)} chars", path=str(path))
        return ExecResult(False, tool, f"unsupported tool in Phase 1: {tool}")
