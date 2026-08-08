from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.scaffold import scaffold_fastapi_health


def test_scaffold_fastapi_health_tree(workspace: Path) -> None:
    root = ws.create_project(workspace, "app1")
    written = scaffold_fastapi_health(root, name="app1")
    assert len(written) >= 10
    main = root / "backend" / "app" / "main.py"
    assert main.is_file()
    text = main.read_text(encoding="utf-8")
    assert "/health" in text
    assert "FastAPI" in text
    assert "/api/v1/ping" in text
    assert (root / "backend" / "tests" / "test_health.py").is_file()
    assert "test_api_ping" in (root / "backend" / "tests" / "test_health.py").read_text(
        encoding="utf-8"
    )
    assert (root / "backend" / "requirements.txt").is_file()
    assert (root / "backend" / "pytest.ini").is_file()
    assert (root / "docker" / "Dockerfile.backend").is_file()
    compose = (root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "healthcheck" in compose
    assert (root / "docs" / "ARCHITECTURE.md").is_file()
    assert (root / "docs" / "API.md").is_file()
    assert "/health" in (root / "README.md").read_text(encoding="utf-8")
    assert (root / "CHANGELOG.md").is_file()
