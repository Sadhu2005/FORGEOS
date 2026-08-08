"""SQLite connection and schema migration for project memory."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from forgeos.core import world_state as ws

MEMORY_FILE = "memory.sqlite"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS project_meta (
    name TEXT PRIMARY KEY,
    phase TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 100,
    dependencies_json TEXT NOT NULL DEFAULT '[]',
    action_json TEXT NOT NULL DEFAULT '{}',
    verification_json TEXT NOT NULL DEFAULT '[]',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    problem TEXT NOT NULL DEFAULT '',
    options_json TEXT NOT NULL DEFAULT '[]',
    chosen TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT '',
    risk TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    timestamp TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT ''
);
"""


def memory_path(project: Path) -> Path:
    return ws.forge_dir(project) / MEMORY_FILE


def connect(project: Path) -> sqlite3.Connection:
    """Open (and create parent dirs for) the project memory DB."""
    path = memory_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Create tables if missing."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
