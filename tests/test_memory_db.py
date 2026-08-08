from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.memory.database import MEMORY_FILE, connect, memory_path, migrate


def test_memory_path(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "mem-db")
    path = memory_path(root)
    assert path.name == MEMORY_FILE
    assert path.parent == ws.forge_dir(root)


def test_migrate_creates_tables(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "mem-db2")
    with connect(root) as conn:
        migrate(conn)
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {"project_meta", "tasks", "decisions", "events"} <= names
    assert memory_path(root).is_file()


def test_connect_idempotent(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "mem-db3")
    with connect(root) as conn:
        conn.execute(
            "INSERT INTO project_meta (name, phase, status, updated_at) VALUES (?,?,?,?)",
            ("mem-db3", "mvp", "active", "2026-01-01T00:00:00Z"),
        )
        conn.commit()
    with connect(root) as conn:
        row = conn.execute("SELECT name FROM project_meta").fetchone()
        assert row["name"] == "mem-db3"
