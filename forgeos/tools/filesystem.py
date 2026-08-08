"""Minimal filesystem tools with path allowlist."""

from __future__ import annotations

import fnmatch
from pathlib import Path


class PathNotAllowedError(PermissionError):
    pass


class FilesystemTool:
    def __init__(self, project_root: Path, write_globs: list[str]) -> None:
        self.project_root = project_root.resolve()
        self.write_globs = write_globs

    def _resolve(self, rel_path: str) -> Path:
        candidate = (self.project_root / rel_path).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise PathNotAllowedError(f"path escapes project root: {rel_path}") from exc
        return candidate

    def allowed_write(self, rel_path: str) -> bool:
        normalized = rel_path.replace("\\", "/")
        for pattern in self.write_globs:
            pat = pattern.replace("\\", "/")
            if fnmatch.fnmatch(normalized, pat):
                return True
            # also allow matching when pattern is a directory prefix like docs/**
            if pat.endswith("/**") and normalized.startswith(pat[:-3]):
                return True
        return False

    def write(self, rel_path: str, content: str) -> Path:
        if not self.allowed_write(rel_path):
            raise PathNotAllowedError(
                f"write not allowed by role for path: {rel_path} (globs={self.write_globs})"
            )
        path = self._resolve(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read(self, rel_path: str) -> str:
        path = self._resolve(rel_path)
        return path.read_text(encoding="utf-8")

    def exists(self, rel_path: str) -> bool:
        return self._resolve(rel_path).exists()
