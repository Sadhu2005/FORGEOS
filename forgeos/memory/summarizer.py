"""Short grounded project summary for LLM context."""

from __future__ import annotations

import json
from pathlib import Path

from forgeos.memory.repository import Repository

DEFAULT_BUDGET = 1000


class Summarizer:
    def __init__(self, project: Path, *, budget: int = DEFAULT_BUDGET) -> None:
        self.project = project.resolve()
        self.budget = budget
        self.repo = Repository(self.project)

    def summarize(self, *, limit: int = 5) -> str:
        """Return completed/pending/blocked counts + last N tasks + last decision."""
        if not self.repo.db_path.exists():
            try:
                self.repo.sync_from_yaml()
            except FileNotFoundError:
                return "Memory: (no project state yet)"

        tasks = self.repo.list_tasks()
        completed = sum(1 for t in tasks if t.get("status") == "COMPLETED")
        blocked = sum(1 for t in tasks if t.get("status") == "BLOCKED")
        pending = sum(
            1
            for t in tasks
            if t.get("status")
            in ("PROPOSED", "READY", "WAITING", "RUNNING", "VERIFYING", "FAILED")
        )

        lines = [
            "## Memory",
            f"Tasks: completed={completed} pending={pending} blocked={blocked} total={len(tasks)}",
        ]

        # Prefer most recently updated tasks (updated_at DESC), then id.
        recent = sorted(
            tasks,
            key=lambda t: (str(t.get("updated_at") or ""), str(t.get("id") or "")),
            reverse=True,
        )[: max(1, limit)]
        if recent:
            lines.append("Recent tasks:")
            for t in recent:
                lines.append(
                    f"- {t.get('id')}: {t.get('status')} — {str(t.get('description') or '')[:80]}"
                )

        decisions = self.repo.list_decisions(limit=1)
        if decisions:
            d = decisions[0]
            chosen = d.get("chosen") or ""
            problem = str(d.get("problem") or "")[:100]
            lines.append(f"Last decision: chosen={chosen}; problem={problem}")
            try:
                opts = json.loads(d.get("options_json") or "[]")
            except json.JSONDecodeError:
                opts = []
            if opts:
                lines.append(f"Options were: {', '.join(str(o) for o in opts)}")

        text = "\n".join(lines)
        if len(text) <= self.budget:
            return text
        return text[: self.budget - 14] + "\n…[truncated]"
