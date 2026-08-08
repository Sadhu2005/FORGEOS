"""Tech-debt scan — TODOs, blocked tasks, approvals, failing tests."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from forgeos.core import world_state as ws
from forgeos.intelligence.health import health_path
from forgeos.planning.task_graph import TaskGraph
from forgeos.safety.approval import ApprovalStore

DEBT_FILE = "debt.yaml"

_SKIP_DIRS = {".forge", ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
_MARKERS = (
    ("TODO", re.compile(r"\bTODO\b")),
    ("FIXME", re.compile(r"\bFIXME\b")),
    ("HACK", re.compile(r"\bHACK\b")),
)
_TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".txt",
    ".rs",
    ".go",
}


def debt_path(project: Path) -> Path:
    return ws.forge_dir(project) / DEBT_FILE


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _score(todo: int, fixme: int, blocked: int, pending: int, failing: int) -> str:
    weight = todo + 2 * fixme + 3 * blocked + 2 * pending + 3 * failing
    if weight >= 15:
        return "high"
    if weight >= 5:
        return "medium"
    return "low"


def scan(project: Path) -> dict[str, Any]:
    """Scan project for debt signals; write .forge/debt.yaml."""
    project = project.resolve()
    todo_count = 0
    fixme_count = 0
    hack_count = 0
    top_hits: list[dict[str, Any]] = []

    for path in project.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(project).parts)
        if parts & _SKIP_DIRS:
            continue
        if path.suffix.lower() not in _TEXT_SUFFIXES and path.name not in {
            "Dockerfile",
            "Makefile",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(project).as_posix()
        for i, line in enumerate(text.splitlines(), 1):
            for name, pattern in _MARKERS:
                if not pattern.search(line):
                    continue
                if name == "TODO":
                    todo_count += 1
                elif name == "FIXME":
                    fixme_count += 1
                else:
                    hack_count += 1
                if len(top_hits) < 20:
                    top_hits.append(
                        {"path": rel, "line": i, "text": line.strip()[:160], "kind": name}
                    )

    graph = TaskGraph.load(ws.tasks_path(project))
    blocked_tasks = sum(1 for t in graph.tasks if t.status == "BLOCKED")
    pending_approvals = len(ApprovalStore(project).list_pending())

    failing_tests = 0
    hp = health_path(project)
    if hp.exists():
        data = yaml.safe_load(hp.read_text(encoding="utf-8")) or {}
        failing_tests = int((data.get("tests") or {}).get("failing") or 0)
    else:
        try:
            state = ws.load(project)
            failing_tests = int((state.get("tests") or {}).get("failing") or 0)
        except FileNotFoundError:
            failing_tests = 0

    # Include HACK in todo weight via fixme-ish bucket for scoring.
    score = _score(
        todo_count,
        fixme_count + hack_count,
        blocked_tasks,
        pending_approvals,
        failing_tests,
    )
    report = {
        "timestamp": _utc_now(),
        "todo_count": todo_count,
        "fixme_count": fixme_count + hack_count,
        "blocked_tasks": blocked_tasks,
        "pending_approvals": pending_approvals,
        "failing_tests": failing_tests,
        "score": score,
        "top_hits": top_hits,
    }
    path = debt_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    return report
