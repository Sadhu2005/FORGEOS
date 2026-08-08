from pathlib import Path
from unittest.mock import patch

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.scaffold import scaffold_fastapi_health

def test_compose_has_postgres_profile(workspace: Path) -> None:
    root = ws.create_project(workspace, "db1")
    scaffold_fastapi_health(root)
    compose = (root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "postgres:" in compose
    assert 'profiles: ["db"]' in compose or "profiles:\n      - db" in compose
    assert "pg_isready" in compose
    assert "forgeos_pgdata" in compose
    assert "/api/v1/ping" in (root / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert "database" in (root / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert not (root / ".env.example").exists()


def test_with_db_writes_env_example(workspace: Path) -> None:
    root = ws.create_project(workspace, "db2")
    scaffold_fastapi_health(root, with_db=True)
    env = root / ".env.example"
    assert env.is_file()
    assert "DATABASE_URL" in env.read_text(encoding="utf-8")
    assert "profile db" in (root / "README.md").read_text(encoding="utf-8").lower() or "--profile db" in (
        root / "README.md"
    ).read_text(encoding="utf-8")


def test_cli_init_with_db(workspace: Path, capsys) -> None:
    assert main(["init", "db-cli", "--scaffold", "--with-db"]) == 0
    out = capsys.readouterr().out
    assert "Postgres" in out or "scaffolded" in out.lower()
    root = ws.project_root(workspace, "db-cli")
    assert (root / ".env.example").is_file()
    assert (root / "docker" / "docker-compose.yml").is_file()


def test_cli_with_db_implies_scaffold(workspace: Path) -> None:
    assert main(["init", "db-impl", "--with-db"]) == 0
    root = ws.project_root(workspace, "db-impl")
    assert (root / "backend" / "app" / "main.py").is_file()
    assert (root / ".env.example").is_file()


def _load_scaffold_app(root: Path):
    import sys

    sys.path.insert(0, str(root / "backend"))
    for mod in list(sys.modules):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]
    from app import main as app_main

    return app_main


def _unload_scaffold_app(root: Path) -> None:
    import sys

    if str(root / "backend") in sys.path:
        sys.path.remove(str(root / "backend"))
    for mod in list(sys.modules):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]


def test_health_skipped_without_url(workspace: Path, monkeypatch) -> None:
    root = ws.create_project(workspace, "db3")
    scaffold_fastapi_health(root)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    try:
        app_main = _load_scaffold_app(root)
        assert app_main._database_status() == "skipped"
        body = app_main.health()
        assert body["database"] == "skipped"
        assert body["status"] == "ok"
    finally:
        _unload_scaffold_app(root)


def test_health_database_ok_and_error_paths(workspace: Path, monkeypatch) -> None:
    root = ws.create_project(workspace, "db5")
    scaffold_fastapi_health(root)
    monkeypatch.setenv("DATABASE_URL", "postgresql://forgeos:forgeos@localhost:5432/forgeos")
    try:
        app_main = _load_scaffold_app(root)

        class _Cur:
            def execute(self, *_a, **_k):
                return None

            def fetchone(self):
                return (1,)

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

        class _Conn:
            def cursor(self):
                return _Cur()

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

        import types
        import sys

        fake = types.ModuleType("psycopg")
        fake.connect = lambda *a, **k: _Conn()  # type: ignore[attr-defined]
        with patch.dict(sys.modules, {"psycopg": fake}):
            assert app_main._database_status() == "ok"
            assert app_main.health()["database"] == "ok"

        fake_err = types.ModuleType("psycopg")

        def _boom(*_a, **_k):
            raise RuntimeError("down")

        fake_err.connect = _boom  # type: ignore[attr-defined]
        with patch.dict(sys.modules, {"psycopg": fake_err}):
            assert app_main._database_status() == "error"
            assert app_main.health()["database"] == "error"
    finally:
        _unload_scaffold_app(root)


def test_default_scaffold_has_ping_and_health(workspace: Path) -> None:
    root = ws.create_project(workspace, "db6")
    scaffold_fastapi_health(root)
    main_py = (root / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert "/api/v1/ping" in main_py
    assert "/health" in main_py
    assert "psycopg" in (root / "backend" / "requirements.txt").read_text(encoding="utf-8")
