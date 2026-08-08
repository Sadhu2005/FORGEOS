"""Load and validate roles/*.yaml policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FIELDS = (
    "id",
    "name",
    "purpose",
    "writes",
    "allowed_tools",
    "forbidden",
    "definition_of_done",
)


@dataclass
class RolePolicy:
    id: str
    name: str
    purpose: str
    writes: list[str]
    allowed_tools: list[str]
    forbidden: list[str]
    definition_of_done: list[str]
    may_commit_feature_branch: bool = False
    requires_human_for_critical: bool = True
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def repo_roles_dir(workspace: Path) -> Path:
    return workspace / "roles"


def load_role(workspace: Path, role_id: str) -> RolePolicy:
    path = repo_roles_dir(workspace) / f"{role_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"role policy not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    validate_role_dict(data)
    return RolePolicy(
        id=data["id"],
        name=data["name"],
        purpose=data["purpose"],
        writes=list(data["writes"]),
        allowed_tools=list(data["allowed_tools"]),
        forbidden=list(data["forbidden"]),
        definition_of_done=list(data["definition_of_done"]),
        may_commit_feature_branch=bool(data.get("may_commit_feature_branch", False)),
        requires_human_for_critical=bool(data.get("requires_human_for_critical", True)),
        raw=data,
    )


def validate_role_dict(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("role policy must be a mapping")
    for key in REQUIRED_FIELDS:
        if key not in data:
            raise ValueError(f"role policy missing required field: {key}")
    if not isinstance(data["writes"], list) or not data["writes"]:
        raise ValueError("role.writes must be a non-empty list")
    if not isinstance(data["allowed_tools"], list):
        raise ValueError("role.allowed_tools must be a list")
    if not isinstance(data["forbidden"], list):
        raise ValueError("role.forbidden must be a list")
    if not isinstance(data["definition_of_done"], list):
        raise ValueError("role.definition_of_done must be a list")
    if data["id"] != Path(str(data.get("_source", data["id"]))).stem and False:
        pass  # id is authoritative from file content


def list_roles(workspace: Path) -> list[str]:
    directory = repo_roles_dir(workspace)
    if not directory.exists():
        return []
    return sorted(p.stem for p in directory.glob("*.yaml"))
