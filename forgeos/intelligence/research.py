"""Local research — search project docs/reports (no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_SEARCH_ROOTS = ("docs", "docs/decisions", ".forge/reports")
_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}


def search(project: Path, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Return ranked path:line snippets matching query under docs/ and reports/."""
    project = project.resolve()
    q = (query or "").strip()
    if not q:
        return []
    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    roots: list[Path] = []
    for rel in _SEARCH_ROOTS:
        candidate = project / rel
        if candidate.exists():
            roots.append(candidate)
    # Also allow top-level docs only once.
    if not roots and (project / "docs").exists():
        roots.append(project / "docs")

    for base in roots:
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if set(path.relative_to(project).parts) & _SKIP_DIRS:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pyc", ".exe"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if q not in text and q.lower() not in text.lower():
                continue
            rel = path.relative_to(project).as_posix()
            for i, line in enumerate(text.splitlines(), 1):
                if q in line or q.lower() in line.lower():
                    key = (rel, i)
                    if key in seen:
                        continue
                    seen.add(key)
                    hits.append(
                        {
                            "path": rel,
                            "line": i,
                            "text": line.strip()[:200],
                        }
                    )
                    if len(hits) >= limit:
                        return hits
    return hits
