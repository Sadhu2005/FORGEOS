"""Validate LLM-produced tasks against role tool allowlists."""

from __future__ import annotations

from pathlib import Path

import yaml

from forgeos.planning.task_graph import Task


def load_role_allowed_tools(roles_dir: Path) -> dict[str, set[str]]:
    """Map role id → allowed_tools from roles/*.yaml."""
    mapping: dict[str, set[str]] = {}
    if not roles_dir.is_dir():
        return mapping
    for path in sorted(roles_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except OSError:
            continue
        if not isinstance(data, dict):
            continue
        rid = str(data.get("id") or path.stem)
        tools = data.get("allowed_tools") or []
        if isinstance(tools, list):
            mapping[rid] = {str(t) for t in tools}
    return mapping


def validate_llm_tasks(
    tasks: list[Task],
    roles_dir: Path | None,
) -> list[Task] | None:
    """Return tasks if every role/tool is allowlisted; else None (caller uses seed)."""
    if not tasks:
        return None
    role_tools = load_role_allowed_tools(roles_dir) if roles_dir is not None else {}
    if not role_tools:
        # No policies loaded — still require action.tool present
        for task in tasks:
            tool = (task.action or {}).get("tool")
            if not tool:
                return None
        return tasks
    for task in tasks:
        role = task.role or ""
        if role not in role_tools:
            return None
        tool = (task.action or {}).get("tool")
        if not tool or str(tool) not in role_tools[role]:
            return None
    return tasks
