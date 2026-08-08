"""Observe project reality after an action."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forgeos.tools.filesystem import FilesystemTool


@dataclass
class Observation:
    path: str
    exists: bool
    size: int
    notes: list[str]


class Observer:
    def __init__(self, fs: FilesystemTool) -> None:
        self.fs = fs

    def observe_file(self, rel_path: str) -> Observation:
        notes: list[str] = []
        exists = self.fs.exists(rel_path)
        size = 0
        if exists:
            full = (self.fs.project_root / rel_path).resolve()
            size = full.stat().st_size
            notes.append("file present")
            if size > 0:
                notes.append("file non-empty")
            else:
                notes.append("file empty")
        else:
            notes.append("file missing")
        return Observation(path=rel_path, exists=exists, size=size, notes=notes)

    def observe_state_file(self, state_file: Path) -> Observation:
        exists = state_file.exists()
        size = state_file.stat().st_size if exists else 0
        return Observation(
            path=str(state_file),
            exists=exists,
            size=size,
            notes=["state.yaml present" if exists else "state.yaml missing"],
        )
