"""Execute validated tool actions via registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forgeos.roles.loader import RolePolicy
from forgeos.tools.base import ToolResult
from forgeos.tools.registry import ToolRegistry


@dataclass
class ExecResult:
    ok: bool
    tool: str
    detail: str
    path: str | None = None
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def from_tool(cls, result: ToolResult) -> ExecResult:
        return cls(
            ok=result.ok,
            tool=result.tool,
            detail=result.detail,
            path=result.path,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            data=result.data,
        )


class Executor:
    def __init__(self, project_root: Path, role: RolePolicy, registry: ToolRegistry | None = None) -> None:
        self.role = role
        self.project_root = project_root.resolve()
        self.registry = registry or ToolRegistry(self.project_root, role)
        # Back-compat for observer/tests that expect .fs
        self.fs = self.registry.fs

    def execute(self, action: dict[str, Any]) -> ExecResult:
        try:
            result = self.registry.dispatch(action)
        except Exception as exc:  # noqa: BLE001 — surface tool errors as ExecResult
            return ExecResult(False, str(action.get("tool", "")), str(exc))
        return ExecResult.from_tool(result)
