"""Append-only audit trail (JSONL + memory events)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgeos.core import world_state as ws
from forgeos.memory.repository import Repository

AUDIT_FILE = "audit.jsonl"


def audit_path(project: Path) -> Path:
    return ws.forge_dir(project) / AUDIT_FILE


class AuditLog:
    def __init__(self, project: Path) -> None:
        self.project = project.resolve()
        self.path = audit_path(self.project)
        self.memory = Repository(self.project)

    def append(
        self,
        kind: str,
        message: str,
        *,
        task_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Write one JSONL line and dual-write a memory event."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        record = {
            "timestamp": ts,
            "kind": kind,
            "task_id": task_id,
            "message": message,
            "payload": payload or {},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        try:
            self.memory.add_event(
                kind=kind,
                task_id=task_id,
                payload={"message": message, **(payload or {})},
            )
        except Exception:
            # Memory DB is best-effort for audit dual-write.
            pass
        return record

    def read_lines(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-max(1, limit) :]:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
