"""Testing tool — run pytest inside project sandbox."""

from __future__ import annotations

import sys
from pathlib import Path

from forgeos.tools.base import ToolResult
from forgeos.tools.terminal import TerminalTool


class TestingTool:
    __test__ = False  # prevent pytest collecting this as a test class

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.terminal = TerminalTool(self.project_root, timeout_s=120.0)

    def run(self, args: list[str] | None = None) -> ToolResult:
        argv = args if args is not None else ["-q"]
        # Prefer current interpreter's pytest module
        cmd_parts = [f'"{sys.executable}"', "-m", "pytest", *argv]
        command = " ".join(cmd_parts)
        result = self.terminal.execute(command, timeout_s=120.0)
        result.tool = "testing.run"
        return result
