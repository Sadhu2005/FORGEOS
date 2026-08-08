"""World state I/O for projects/<name>/.forge/state.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

FORGE_DIR = ".forge"
STATE_FILE = "state.yaml"
TASKS_FILE = "tasks.yaml"


def project_root(workspace: Path, name: str) -> Path:
    return (workspace / "projects" / name).resolve()


def forge_dir(project: Path) -> Path:
    return project / FORGE_DIR


def state_path(project: Path) -> Path:
    return forge_dir(project) / STATE_FILE


def tasks_path(project: Path) -> Path:
    return forge_dir(project) / TASKS_FILE


def reports_dir(project: Path) -> Path:
    return forge_dir(project) / "reports"


def default_state(name: str) -> dict[str, Any]:
    return {
        "project": {
            "name": name,
            "phase": "mvp",
            "status": "active",
        },
        "repository": {
            "branch": "main",
            "clean": True,
            "last_commit": "",
        },
        "architecture": {},
        "tasks": {
            "completed": 0,
            "pending": 0,
            "blocked": 0,
        },
        "tests": {
            "total": 0,
            "passing": 0,
            "failing": 0,
        },
        "environment": {},
    }


def create_project(workspace: Path, name: str) -> Path:
    """Create projects/<name>/.forge/state.yaml and empty tasks/reports dirs."""
    root = project_root(workspace, name)
    if state_path(root).exists():
        raise FileExistsError(f"Project already exists: {root}")
    forge_dir(root).mkdir(parents=True, exist_ok=True)
    reports_dir(root).mkdir(parents=True, exist_ok=True)
    save(root, default_state(name))
    tasks_path(root).write_text("tasks: []\n", encoding="utf-8")
    return root


def load(project: Path) -> dict[str, Any]:
    path = state_path(project)
    if not path.exists():
        raise FileNotFoundError(f"Missing world state: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    _validate_minimal(data)
    return data


def save(project: Path, state: dict[str, Any]) -> None:
    _validate_minimal(state)
    forge_dir(project).mkdir(parents=True, exist_ok=True)
    path = state_path(project)
    path.write_text(
        yaml.safe_dump(state, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _validate_minimal(state: dict[str, Any]) -> None:
    for key in ("project", "repository", "tasks"):
        if key not in state:
            raise ValueError(f"world state missing required key: {key}")
    project = state["project"]
    for key in ("name", "phase", "status"):
        if key not in project:
            raise ValueError(f"world state.project missing required key: {key}")
