"""Observe project reality after an action."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forgeos.tools.filesystem import FilesystemTool


@dataclass
class Observation:
    path: str
    exists: bool
    size: int
    notes: list[str]
    content: str = ""
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    tool: str = ""
    detail: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class Observer:
    def __init__(self, fs: FilesystemTool) -> None:
        self.fs = fs

    def observe_file(self, rel_path: str) -> Observation:
        notes: list[str] = []
        exists = self.fs.exists(rel_path) if rel_path else False
        size = 0
        content = ""
        if exists and rel_path:
            full = (self.fs.project_root / rel_path).resolve()
            size = full.stat().st_size
            notes.append("file present")
            if size > 0:
                notes.append("file non-empty")
                try:
                    content = full.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    content = ""
            else:
                notes.append("file empty")
        else:
            notes.append("file missing")
        return Observation(path=rel_path, exists=exists, size=size, notes=notes, content=content)

    def observe_exec(self, result: Any) -> Observation:
        """Build observation from ExecResult / ToolResult-like object."""
        exit_code = getattr(result, "exit_code", None)
        stdout = getattr(result, "stdout", "") or ""
        stderr = getattr(result, "stderr", "") or ""
        detail = getattr(result, "detail", "") or ""
        tool = getattr(result, "tool", "") or ""
        path = getattr(result, "path", None) or ""
        ok = bool(getattr(result, "ok", False))
        notes = [
            f"tool={tool}" if tool else "tool=unknown",
            f"exit_code={exit_code}",
            "exec ok" if ok else "exec failed",
        ]
        if detail:
            notes.append(detail)
        return Observation(
            path=str(path),
            exists=ok,
            size=len(stdout),
            notes=notes,
            content=stdout,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            tool=tool,
            detail=detail,
        )

    def observe_state_file(self, state_file: Path) -> Observation:
        exists = state_file.exists()
        size = state_file.stat().st_size if exists else 0
        return Observation(
            path=str(state_file),
            exists=exists,
            size=size,
            notes=["state.yaml present" if exists else "state.yaml missing"],
        )
