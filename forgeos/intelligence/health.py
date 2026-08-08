"""Project health probe — tests, environment, compose config."""

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from forgeos.core import world_state as ws
from forgeos.tools.docker import DockerTool
from forgeos.tools.testing import TestingTool

HEALTH_FILE = "health.yaml"

_PYTEST_SUMMARY = re.compile(
    r"=+\s*(?:(\d+)\s+passed)?(?:,\s*)?(?:(\d+)\s+failed)?(?:,\s*)?(?:(\d+)\s+error)?",
    re.I,
)


def health_path(project: Path) -> Path:
    return ws.forge_dir(project) / HEALTH_FILE


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_tests_root(project: Path) -> Path | None:
    for candidate in (project / "tests", project / "backend" / "tests"):
        if candidate.is_dir():
            return candidate
    return None


def _parse_pytest_counts(output: str) -> tuple[int, int, int]:
    """Return (passed, failed, errors) from pytest summary line."""
    passed = failed = errors = 0
    for line in output.splitlines()[::-1]:
        if "passed" in line.lower() or "failed" in line.lower() or "error" in line.lower():
            m = re.search(r"(\d+)\s+passed", line, re.I)
            if m:
                passed = int(m.group(1))
            m = re.search(r"(\d+)\s+failed", line, re.I)
            if m:
                failed = int(m.group(1))
            m = re.search(r"(\d+)\s+error", line, re.I)
            if m:
                errors = int(m.group(1))
            if passed or failed or errors:
                break
    return passed, failed, errors


def probe(project: Path) -> dict[str, Any]:
    """Run health probe; write .forge/health.yaml and update state tests/environment."""
    project = project.resolve()
    notes: list[str] = []
    docker_bin = shutil.which("docker")
    env = {
        "python": sys.version.split()[0],
        "docker": bool(docker_bin),
        "compose_config_ok": False,
    }

    compose = project / "docker" / "docker-compose.yml"
    if compose.exists():
        result = DockerTool(project).compose_config("docker/docker-compose.yml")
        env["compose_config_ok"] = bool(result.ok)
        if not result.ok:
            notes.append(f"compose_config: {result.detail}")
    else:
        notes.append("no docker/docker-compose.yml")

    tests_info: dict[str, Any] = {
        "total": 0,
        "passing": 0,
        "failing": 0,
        "detail": "no tests tree",
    }
    tests_root = _find_tests_root(project)
    if tests_root is None:
        notes.append("no tests tree")
    else:
        rel = tests_root.relative_to(project).as_posix()
        # Collect-only first to avoid long hangs; then full run if collection works.
        collect = TestingTool(project).run(["-q", "--collect-only", "-q", rel])
        if not collect.ok and "no tests ran" not in (collect.stdout or "").lower():
            # Still try a quiet run — empty suites may exit non-zero.
            notes.append(f"collect: {collect.detail}")
        run = TestingTool(project).run(["-q", rel])
        out = f"{run.stdout or ''}\n{run.stderr or ''}"
        passed, failed, errors = _parse_pytest_counts(out)
        failing = failed + errors
        total = passed + failing
        if total == 0 and run.ok:
            # Collected zero or summary missing — treat as empty suite.
            notes.append("pytest ran with no counted results")
        tests_info = {
            "total": total,
            "passing": passed,
            "failing": failing,
            "detail": f"pytest exit={run.exit_code} under {rel}",
        }

    report = {
        "timestamp": _utc_now(),
        "tests": tests_info,
        "environment": env,
        "notes": notes,
    }

    path = health_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")

    try:
        state = ws.load(project)
    except FileNotFoundError:
        return report
    state["tests"] = {
        "total": int(tests_info["total"]),
        "passing": int(tests_info["passing"]),
        "failing": int(tests_info["failing"]),
    }
    state["environment"] = {
        **dict(state.get("environment") or {}),
        "python": env["python"],
        "docker": env["docker"],
        "compose_config_ok": env["compose_config_ok"],
    }
    ws.save(project, state)
    return report
