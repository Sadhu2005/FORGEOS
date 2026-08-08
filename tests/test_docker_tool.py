from pathlib import Path
from unittest.mock import MagicMock, patch

from forgeos.core import world_state as ws
from forgeos.tools.docker import DockerTool


def test_compose_config_missing_file(workspace: Path) -> None:
    root = ws.create_project(workspace, "dock")
    tool = DockerTool(root)
    result = tool.compose_config("docker/docker-compose.yml")
    assert not result.ok
    assert "missing" in result.detail


def test_compose_config_mocked(workspace: Path) -> None:
    root = ws.create_project(workspace, "dock2")
    compose = root / "docker" / "docker-compose.yml"
    compose.parent.mkdir(parents=True)
    compose.write_text("services:\n  web:\n    image: nginx\n", encoding="utf-8")
    tool = DockerTool(root)

    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = "name: dock2\nservices:\n  web: {}\n"
    fake.stderr = ""

    with (
        patch("forgeos.tools.docker.shutil.which", return_value="docker"),
        patch("forgeos.tools.docker.subprocess.run", return_value=fake) as run,
    ):
        result = tool.compose_config("docker/docker-compose.yml")
    assert result.ok
    assert result.tool == "docker.compose_config"
    run.assert_called_once()
    args = run.call_args[0][0]
    assert args[0] == "docker"
    assert "compose" in args
    assert "config" in args
