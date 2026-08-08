"""Docker tools — compose config + approval-gated compose up."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from forgeos.tools.base import ToolResult


class DockerTool:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def _resolve_compose(self, compose_file: str, tool: str) -> tuple[Path | None, ToolResult | None]:
        path = (self.project_root / compose_file).resolve()
        try:
            path.relative_to(self.project_root)
        except ValueError:
            return None, ToolResult(False, tool, "compose path escapes project")
        if not path.exists():
            return None, ToolResult(
                False,
                tool,
                f"compose file missing: {compose_file}",
                path=str(path),
            )
        return path, None

    def compose_config(self, compose_file: str = "docker/docker-compose.yml") -> ToolResult:
        path, err = self._resolve_compose(compose_file, "docker.compose_config")
        if err:
            return err
        assert path is not None
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

    def compose_up(self, compose_file: str = "docker/docker-compose.yml") -> ToolResult:
        """Run compose up -d (caller must have passed approval gate)."""
        path, err = self._resolve_compose(compose_file, "docker.compose_up")
        if err:
            return err
        assert path is not None
        docker = shutil.which("docker")
        if not docker:
            return ToolResult(
                False,
                "docker.compose_up",
                "docker binary not found on PATH",
                path=str(path),
            )
        # Prefer dry-run when supported; fall back to real up -d.
        dry = subprocess.run(
            [docker, "compose", "-f", str(path), "up", "-d", "--dry-run"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )
        if dry.returncode == 0:
            return ToolResult(
                True,
                "docker.compose_up",
                "dry-run ok",
                path=str(path),
                exit_code=0,
                stdout=(dry.stdout or "")[-8000:],
                stderr=(dry.stderr or "")[-4000:],
            )
        completed = subprocess.run(
            [docker, "compose", "-f", str(path), "up", "-d"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )
        return ToolResult(
            ok=completed.returncode == 0,
            tool="docker.compose_up",
            detail=f"exit={completed.returncode}",
            path=str(path),
            exit_code=completed.returncode,
            stdout=(completed.stdout or "")[-8000:],
            stderr=(completed.stderr or "")[-4000:],
        )
