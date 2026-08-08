"""Terminal execute tool with project cwd sandbox and deny list."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from forgeos.tools.base import ToolResult

DENY_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+\\",
        r"\bformat\s+",
        r"\bmkfs\b",
        r"\bshutdown\b",
        r"\breboot\b",
        r"del\s+/s\s+/q\s+C:",
        r"Remove-Item\s+-Recurse\s+-Force\s+C:\\",
        r"git\s+push\s+.*--force",
        r"git\s+push\s+-f\b",
        r"git\s+reset\s+--hard",
    )
]


class TerminalDeniedError(PermissionError):
    pass


class TerminalTool:
    def __init__(self, project_root: Path, timeout_s: float = 60.0) -> None:
        self.project_root = project_root.resolve()
        self.timeout_s = timeout_s

    def _assert_safe(self, command: str) -> None:
        for pat in DENY_PATTERNS:
            if pat.search(command):
                raise TerminalDeniedError(f"command denied by policy: {command}")

    def execute(
        self,
        command: str,
        timeout_s: float | None = None,
        *,
        cwd: str | Path | None = None,
    ) -> ToolResult:
        self._assert_safe(command)
        timeout = timeout_s if timeout_s is not None else self.timeout_s
        work = self.project_root
        if cwd is not None:
            candidate = (self.project_root / Path(cwd)).resolve()
            try:
                candidate.relative_to(self.project_root)
            except ValueError:
                return ToolResult(False, "terminal.execute", "cwd escapes project")
            if not candidate.is_dir():
                return ToolResult(False, "terminal.execute", f"cwd missing: {cwd}")
            work = candidate
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(work),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return ToolResult(
                ok=False,
                tool="terminal.execute",
                detail=f"timeout after {timeout}s",
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
                exit_code=None,
            )
        out = (completed.stdout or "")[-8000:]
        err = (completed.stderr or "")[-4000:]
        return ToolResult(
            ok=completed.returncode == 0,
            tool="terminal.execute",
            detail=f"exit={completed.returncode}",
            exit_code=completed.returncode,
            stdout=out,
            stderr=err,
            data={"cwd": str(work)},
        )
