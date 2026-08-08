"""Filesystem tools with path allowlist (Phase 1 + Phase 2 expansions)."""

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
            if pat.endswith("/**") and (
                normalized.startswith(pat[:-3]) or normalized == pat[:-3].rstrip("/")
            ):
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

    def edit(self, rel_path: str, old: str, new: str) -> Path:
        """Replace first occurrence of old with new; write full file if missing and old empty."""
        if not self.allowed_write(rel_path):
            raise PathNotAllowedError(f"edit not allowed for path: {rel_path}")
        path = self._resolve(rel_path)
        if not path.exists():
            if old:
                raise FileNotFoundError(f"cannot edit missing file: {rel_path}")
            return self.write(rel_path, new)
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise ValueError(f"edit target string not found in {rel_path}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return path

    def search(self, query: str, root: str = ".", max_hits: int = 50) -> list[dict]:
        base = self._resolve(root) if root not in (".", "") else self.project_root
        hits: list[dict] = []
        if not base.exists():
            return hits
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".exe", ".dll", ".pyc"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if query not in text:
                continue
            rel = path.relative_to(self.project_root).as_posix()
            line_no = next(
                (i for i, line in enumerate(text.splitlines(), 1) if query in line),
                0,
            )
            hits.append({"path": rel, "line": line_no})
            if len(hits) >= max_hits:
                break
        return hits

    def tree(self, root: str = ".", max_depth: int = 3) -> list[str]:
        base = self._resolve(root) if root not in (".", "") else self.project_root
        lines: list[str] = []
        if not base.exists():
            return lines

        def walk(current: Path, depth: int) -> None:
            if depth > max_depth:
                return
            try:
                entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except OSError:
                return
            for entry in entries:
                if entry.name in {".git", "__pycache__", ".venv", "node_modules"}:
                    continue
                rel = entry.relative_to(self.project_root).as_posix()
                prefix = "  " * depth
                lines.append(f"{prefix}{rel}{'/' if entry.is_dir() else ''}")
                if entry.is_dir():
                    walk(entry, depth + 1)

        walk(base, 0)
        return lines

    def delete(self, rel_path: str) -> Path:
        if not self.allowed_write(rel_path):
            raise PathNotAllowedError(f"delete not allowed for path: {rel_path}")
        path = self._resolve(rel_path)
        if not path.exists():
            raise FileNotFoundError(f"missing: {rel_path}")
        if path.is_dir():
            if any(path.iterdir()):
                raise IsADirectoryError(f"refuse non-empty directory delete: {rel_path}")
            path.rmdir()
        else:
            path.unlink()
        return path
