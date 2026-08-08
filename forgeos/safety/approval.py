"""File-based approval queue under .forge/approvals/."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from forgeos.core import world_state as ws
from forgeos.safety.permissions import fingerprint as make_fingerprint

APPROVALS_DIR = "approvals"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ApprovalStore:
    def __init__(self, project: Path) -> None:
        self.project = project.resolve()
        self.dir = ws.forge_dir(self.project) / APPROVALS_DIR

    def _path(self, approval_id: str) -> Path:
        return self.dir / f"{approval_id}.yaml"

    def request(
        self,
        *,
        project_name: str,
        task_id: str,
        action: dict[str, Any],
        risk: str,
        reason: str,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        self.dir.mkdir(parents=True, exist_ok=True)
        tool = str(action.get("tool") or "")
        fp = make_fingerprint(task_id, action)
        # Reuse existing pending ticket for same fingerprint.
        for ticket in self.list_all():
            if ticket.get("fingerprint") == fp and ticket.get("status") == "pending":
                return ticket
        aid = approval_id or f"appr-{uuid.uuid4().hex[:12]}"
        ticket = {
            "id": aid,
            "project": project_name,
            "task_id": task_id,
            "tool": tool,
            "fingerprint": fp,
            "status": "pending",
            "risk": risk or "critical",
            "reason": reason,
            "created_at": _utc_now(),
            "resolved_at": None,
            "action": dict(action),
        }
        self._path(aid).write_text(
            yaml.safe_dump(ticket, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return ticket

    def _load(self, approval_id: str) -> dict[str, Any]:
        path = self._path(approval_id)
        if not path.exists():
            raise FileNotFoundError(f"approval not found: {approval_id}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"invalid approval file: {path}")
        return data

    def _save(self, ticket: dict[str, Any]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        aid = str(ticket["id"])
        self._path(aid).write_text(
            yaml.safe_dump(ticket, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    def list_all(self) -> list[dict[str, Any]]:
        if not self.dir.exists():
            return []
        tickets: list[dict[str, Any]] = []
        for path in sorted(self.dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict) and data.get("id"):
                tickets.append(data)
        return tickets

    def list_pending(self) -> list[dict[str, Any]]:
        return [t for t in self.list_all() if t.get("status") == "pending"]

    def is_approved(self, fingerprint: str) -> bool:
        for ticket in self.list_all():
            if ticket.get("fingerprint") == fingerprint and ticket.get("status") == "approved":
                return True
        return False

    def find_by_fingerprint(self, fingerprint: str) -> dict[str, Any] | None:
        matches = [t for t in self.list_all() if t.get("fingerprint") == fingerprint]
        if not matches:
            return None
        # Prefer approved, then pending, then latest.
        for status in ("approved", "pending", "rejected"):
            for ticket in reversed(matches):
                if ticket.get("status") == status:
                    return ticket
        return matches[-1]

    def approve(self, approval_id: str) -> dict[str, Any]:
        ticket = self._load(approval_id)
        if ticket.get("status") == "rejected":
            raise ValueError(f"approval already rejected: {approval_id}")
        ticket["status"] = "approved"
        ticket["resolved_at"] = _utc_now()
        self._save(ticket)
        return ticket

    def reject(self, approval_id: str) -> dict[str, Any]:
        ticket = self._load(approval_id)
        if ticket.get("status") == "approved":
            raise ValueError(f"approval already approved: {approval_id}")
        ticket["status"] = "rejected"
        ticket["resolved_at"] = _utc_now()
        self._save(ticket)
        return ticket
