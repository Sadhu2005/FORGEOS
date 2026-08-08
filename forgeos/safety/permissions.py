"""Central permission gate for critical tools and task risk."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from forgeos.roles.loader import RolePolicy

DecisionKind = Literal["allow", "deny", "need_approval"]

CRITICAL_TOOLS = frozenset({"filesystem.delete", "docker.compose_up"})
CRITICAL_RISKS = frozenset({"high", "critical"})
PROTECTED_BRANCHES = frozenset({"main", "master"})


@dataclass(frozen=True)
class PermissionDecision:
    kind: DecisionKind
    reason: str
    risk: str = "low"


def fingerprint(task_id: str, action: dict[str, Any]) -> str:
    tool = str(action.get("tool") or "")
    detail = str(action.get("path") or action.get("command") or action.get("message") or "")
    return f"{task_id}:{tool}:{detail}"


def check(
    role: RolePolicy,
    action: dict[str, Any],
    *,
    task_risk: str = "low",
    branch: str = "",
) -> PermissionDecision:
    """Decide allow / deny / need_approval for a tool action."""
    tool = str(action.get("tool") or "")
    risk = (task_risk or "low").lower()

    if not tool:
        return PermissionDecision("deny", "missing action.tool", risk=risk)

    if tool not in role.allowed_tools:
        return PermissionDecision(
            "deny",
            f"tool not allowed by role {role.id}: {tool}",
            risk=risk,
        )

    critical = False
    reason_parts: list[str] = []

    if risk in CRITICAL_RISKS:
        critical = True
        reason_parts.append(f"task risk {risk}")

    if tool in CRITICAL_TOOLS:
        critical = True
        reason_parts.append(f"critical tool {tool}")

    if tool == "git.commit":
        branch_name = (branch or "").strip() or "main"
        if not role.may_commit_feature_branch:
            critical = True
            reason_parts.append(f"role {role.id} may not commit (may_commit_feature_branch=false)")
        if branch_name in PROTECTED_BRANCHES:
            critical = True
            reason_parts.append(f"commit on protected branch {branch_name}")

    if not critical:
        return PermissionDecision("allow", "ok", risk=risk)

    reason = "; ".join(reason_parts) or "critical action"
    if role.requires_human_for_critical:
        return PermissionDecision("need_approval", reason, risk=risk or "critical")
    return PermissionDecision("allow", f"allowed without human gate: {reason}", risk=risk)
