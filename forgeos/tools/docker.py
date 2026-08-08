"""Docker tools — compose config validation only in Phase 2."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from forgeos.tools.base import ToolResult


class DockerTool:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def compose_config(self, compose_file: str = "docker/docker-compose.yml") -> ToolResult:
        path = (self.project_root / compose_file).resolve()
        try:
            path.relative_to(self.project_root)
        except ValueError:
            return ToolResult(False, "docker.compose_config", "compose path escapes project")
        if not path.exists():
            return ToolResult(
                False,
                "docker.compose_config",
                f"compose file missing: {compose_file}",
                path=str(path),
            )
        docker = shutil.which("docker")
        if not docker:
            return ToolResult(
                False,
                "docker.compose_config",
                "docker binary not found on PATH",
                path=str(path),
            )
        completed = subprocess.run(
            [docker, "compose", "-f", str(path), "config"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )
        return ToolResult(
            ok=completed.returncode == 0,
            tool="docker.compose_config",
            detail=f"exit={completed.returncode}",
            path=str(path),
            exit_code=completed.returncode,
            stdout=(completed.stdout or "")[-8000:],
            stderr=(completed.stderr or "")[-4000:],
        )
