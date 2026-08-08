"""Minimal context builder with a hard character budget."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_BUDGET = 8000


@dataclass
class ContextManager:
    """Build a grounded prompt; truncate file tails first when over budget."""

    budget: int = DEFAULT_BUDGET
    project_root: Path | None = None

    def build(
        self,
        *,
        goal: str,
        role_id: str,
        allowed_tools: list[str] | None = None,
        file_paths: list[str] | None = None,
        extra: str = "",
    ) -> str:
        tools = allowed_tools or []
        sections: list[str] = [
            "# FORGEOS context",
            f"Role: {role_id}",
            f"Goal: {goal}",
            "Allowed tools: " + (", ".join(tools) if tools else "(none)"),
        ]
        if extra:
            sections.append(extra.strip())

        file_blocks: list[str] = []
        if self.project_root and file_paths:
            for rel in file_paths:
                path = (self.project_root / rel).resolve()
                try:
                    path.relative_to(self.project_root.resolve())
                except ValueError:
                    continue
                if not path.is_file():
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                file_blocks.append(f"## File: {rel}\n{text}")

        header = "\n".join(sections)
        body = "\n\n".join(file_blocks)
        prompt = header if not body else f"{header}\n\n{body}"
        return self._truncate(prompt)

    def _truncate(self, prompt: str) -> str:
        if len(prompt) <= self.budget:
            return prompt
        # Prefer keeping the header (before first ## File) and trimming file tails.
        marker = "\n## File:"
        if marker in prompt:
            head, _, rest = prompt.partition(marker)
            # Rest still starts after marker; rebuild with truncated files from the end.
            files_blob = marker + rest
            keep_head = head
            available = self.budget - len(keep_head) - 32
            if available <= 0:
                return keep_head[: self.budget]
            truncated_files = files_blob[:available]
            if len(files_blob) > available:
                truncated_files += "\n…[truncated]"
            return keep_head + truncated_files
        return prompt[: self.budget - 14] + "\n…[truncated]"
