"""Optional live Ollama plan — skipped when Ollama is down."""

from __future__ import annotations

from pathlib import Path

import pytest

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.llm.ollama_client import OllamaClient
from forgeos.planning.task_graph import TaskGraph


def _ollama_up() -> bool:
    try:
        return OllamaClient(timeout_s=5.0).ping()
    except Exception:
        return False


@pytest.mark.ollama
@pytest.mark.skipif(not _ollama_up(), reason="Ollama not reachable")
def test_ollama_plan_fastapi_health_bounded(workspace: Path) -> None:
    assert main(["init", "ollama-p11", "--scaffold"]) == 0
    # Force short timeout so CI/machines don't hang if generate stalls
    import os

    os.environ["FORGEOS_OLLAMA_TIMEOUT"] = "90"
    code = main(
        [
            "plan",
            "ollama-p11",
            "--goal",
            "Create a Python FastAPI project with a /health endpoint and tests",
            "--template",
            "fastapi-health",
            "--llm",
            "ollama",
            "--force",
        ]
    )
    assert code == 0
    root = ws.project_root(workspace, "ollama-p11")
    graph = TaskGraph.load(ws.tasks_path(root))
    assert len(graph.tasks) >= 1
    # Seed or LLM plan should include backend/devops style ids or short scaffold graph
    ids = {t.id for t in graph.tasks}
    assert ids & {"be-003", "arch-001", "task-001", "ops-002"} or len(graph.tasks) >= 2
