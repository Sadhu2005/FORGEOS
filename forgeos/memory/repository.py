"""Upsert/query API over per-project SQLite memory."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgeos.core import world_state as ws
from forgeos.memory.database import connect, memory_path
from forgeos.planning.task_graph import Task, TaskGraph


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class Repository:
    def __init__(self, project: Path) -> None:
        self.project = project.resolve()

    @property
    def db_path(self) -> Path:
        return memory_path(self.project)

    def sync_from_yaml(self) -> None:
        """Mirror world state + task graph YAML into SQLite."""
        state = ws.load(self.project)
        graph = TaskGraph.load(ws.tasks_path(self.project))
        now = _utc_now()
        proj = state.get("project") or {}
        with connect(self.project) as conn:
            conn.execute(
                """
                INSERT INTO project_meta (name, phase, status, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    phase=excluded.phase,
                    status=excluded.status,
                    updated_at=excluded.updated_at
                """,
                (
                    str(proj.get("name") or self.project.name),
                    str(proj.get("phase") or ""),
                    str(proj.get("status") or ""),
                    now,
                ),
            )
            for task in graph.tasks:
                self._upsert_task_conn(conn, task, now)
            conn.commit()

    def upsert_task(self, task: Task) -> None:
        now = _utc_now()
        with connect(self.project) as conn:
            self._upsert_task_conn(conn, task, now)
            conn.commit()

    def _upsert_task_conn(self, conn, task: Task, now: str) -> None:
        conn.execute(
            """
            INSERT INTO tasks (
                id, description, status, role, priority,
                dependencies_json, action_json, verification_json,
                attempts, last_error, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                description=excluded.description,
                status=excluded.status,
                role=excluded.role,
                priority=excluded.priority,
                dependencies_json=excluded.dependencies_json,
                action_json=excluded.action_json,
                verification_json=excluded.verification_json,
                attempts=excluded.attempts,
                last_error=excluded.last_error,
                updated_at=excluded.updated_at
            """,
            (
                task.id,
                task.description,
                task.status,
                task.role,
                int(task.priority),
                _dumps(list(task.dependencies)),
                _dumps(dict(task.action)),
                _dumps(list(task.verification)),
                int(task.attempts),
                task.last_error or "",
                now,
            ),
        )

    def list_tasks(self) -> list[dict[str, Any]]:
        with connect(self.project) as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY priority ASC, id ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def add_decision(
        self,
        *,
        problem: str,
        options: list[str],
        chosen: str,
        confidence: str = "",
        risk: str = "",
        reason: str = "",
        evidence: list[str] | None = None,
        decision_id: str | None = None,
        timestamp: str | None = None,
    ) -> str:
        did = decision_id or f"dec-{uuid.uuid4().hex[:12]}"
        ts = timestamp or _utc_now()
        with connect(self.project) as conn:
            conn.execute(
                """
                INSERT INTO decisions (
                    id, problem, options_json, chosen, confidence,
                    risk, reason, evidence_json, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    did,
                    problem,
                    _dumps(list(options)),
                    chosen,
                    confidence,
                    risk,
                    reason,
                    _dumps(list(evidence or [])),
                    ts,
                ),
            )
            conn.commit()
        return did

    def list_decisions(self, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.project) as conn:
            rows = conn.execute(
                """
                SELECT * FROM decisions
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (max(1, limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_event(
        self,
        *,
        kind: str,
        task_id: str = "",
        payload: dict[str, Any] | None = None,
        event_id: str | None = None,
        created_at: str | None = None,
    ) -> str:
        eid = event_id or f"evt-{uuid.uuid4().hex[:12]}"
        ts = created_at or _utc_now()
        with connect(self.project) as conn:
            conn.execute(
                """
                INSERT INTO events (id, task_id, kind, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (eid, task_id, kind, _dumps(payload or {}), ts),
            )
            conn.commit()
        return eid

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        with connect(self.project) as conn:
            rows = conn.execute(
                """
                SELECT * FROM events
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (max(1, limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def counts(self) -> dict[str, int]:
        with connect(self.project) as conn:
            tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            decisions = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
            events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            meta = conn.execute("SELECT COUNT(*) FROM project_meta").fetchone()[0]
        return {
            "project_meta": int(meta),
            "tasks": int(tasks),
            "decisions": int(decisions),
            "events": int(events),
        }
