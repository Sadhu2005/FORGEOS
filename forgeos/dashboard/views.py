"""Dashboard data loading and HTML template rendering."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import yaml

from forgeos.core import world_state as ws
from forgeos.intelligence.debt import debt_path
from forgeos.intelligence.health import health_path
from forgeos.memory.repository import Repository
from forgeos.planning.task_graph import TaskGraph
from forgeos.safety.approval import ApprovalStore
from forgeos.safety.audit import AuditLog
from forgeos.tools.git import GitTool

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"


def escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def list_projects(workspace: Path) -> list[dict[str, str]]:
    root = workspace / "projects"
    if not root.exists():
        return []
    projects: list[dict[str, str]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not ws.state_path(child).exists():
            continue
        try:
            state = ws.load(child)
            proj = state.get("project") or {}
            name = str(proj.get("name") or child.name)
            status = str(proj.get("status") or "")
            phase = str(proj.get("phase") or "")
        except Exception:
            name, status, phase = child.name, "unknown", ""
        projects.append({"name": name, "status": status, "phase": phase, "slug": child.name})
    return projects


def load_yaml_safe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def project_overview(workspace: Path, name: str) -> dict[str, Any]:
    project = ws.project_root(workspace, name)
    state = ws.load(project)
    graph = TaskGraph.load(ws.tasks_path(project))
    counts = graph.update_counts()
    pending = ApprovalStore(project).list_pending()
    health = load_yaml_safe(health_path(project))
    debt = load_yaml_safe(debt_path(project))
    checkpoints = GitTool(project).list_checkpoints()[-5:]
    return {
        "name": name,
        "project": project,
        "state": state,
        "task_counts": counts,
        "task_total": len(graph.tasks),
        "pending_approvals": pending,
        "pending_count": len(pending),
        "health": health,
        "debt": debt,
        "checkpoints": checkpoints,
    }


def project_tasks(workspace: Path, name: str) -> list[dict[str, Any]]:
    project = ws.project_root(workspace, name)
    return TaskGraph.load(ws.tasks_path(project)).to_list()


def project_approvals(workspace: Path, name: str) -> list[dict[str, Any]]:
    project = ws.project_root(workspace, name)
    return ApprovalStore(project).list_pending()


def project_audit(workspace: Path, name: str, limit: int = 50) -> list[dict[str, Any]]:
    project = ws.project_root(workspace, name)
    return AuditLog(project).read_lines(limit=limit)


def project_memory(workspace: Path, name: str) -> dict[str, Any]:
    project = ws.project_root(workspace, name)
    repo = Repository(project)
    if not repo.db_path.exists():
        try:
            repo.sync_from_yaml()
        except FileNotFoundError:
            return {"counts": {}, "decisions": [], "events": []}
    return {
        "counts": repo.counts(),
        "decisions": repo.list_decisions(limit=20),
        "events": repo.recent_events(limit=20),
    }


def _render_partials(template: str, ctx: dict[str, Any]) -> str:
    """Expand {{#each key}}...{{/each}} and {{#if key}}...{{/if}} simply."""

    def each_repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        body = match.group(2)
        items = ctx.get(key) or []
        if not isinstance(items, list):
            return ""
        out: list[str] = []
        for item in items:
            chunk = body
            if isinstance(item, dict):
                for k, v in item.items():
                    chunk = chunk.replace("{{this." + k + "}}", escape(v))
            else:
                chunk = chunk.replace("{{this}}", escape(item))
            out.append(chunk)
        return "".join(out)

    template = re.sub(
        r"\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}",
        each_repl,
        template,
        flags=re.S,
    )

    def if_repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        body = match.group(2)
        val = ctx.get(key)
        truthy = bool(val) if not isinstance(val, (int, float)) else val != 0
        return body if truthy else ""

    template = re.sub(
        r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}",
        if_repl,
        template,
        flags=re.S,
    )
    return template


def render(template_name: str, **ctx: Any) -> str:
    path = TEMPLATES_DIR / template_name
    body = path.read_text(encoding="utf-8")
    body = _render_partials(body, ctx)
    for key, value in ctx.items():
        if isinstance(value, (dict, list)):
            continue
        body = body.replace("{{" + key + "}}", escape(value))
    body = re.sub(r"\{\{[^}]+\}\}", "", body)

    if template_name == "base.html":
        return body

    base = (TEMPLATES_DIR / "base.html").read_text(encoding="utf-8")
    # Insert body before wrapping escapes title etc.
    page = base.replace("{{content}}", body)
    for key, value in ctx.items():
        if isinstance(value, (dict, list)):
            continue
        page = page.replace("{{" + key + "}}", escape(value))
    page = re.sub(r"\{\{[^}]+\}\}", "", page)
    return page
