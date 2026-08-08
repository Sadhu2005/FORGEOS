from pathlib import Path
from unittest.mock import MagicMock, patch

from forgeos.cli import main
from forgeos.core import world_state as ws


def test_llm_status_mocked(workspace: Path, capsys) -> None:
    client = MagicMock()
    client.list_models.return_value = ["qwen3:4b", "qwen2.5-coder:7b"]
    with patch("forgeos.cli.OllamaClient", return_value=client):
        assert main(["llm", "status"]) == 0
    out = capsys.readouterr().out
    assert "reachable: true" in out
    assert "qwen3:4b" in out
    assert "coding:" in out


def test_llm_complete_mocked(workspace: Path, capsys) -> None:
    with patch("forgeos.cli.ModelRouter") as router_cls:
        router = MagicMock()
        router.complete.return_value = "OK"
        router.current_model = "qwen2.5-coder:7b"
        router_cls.return_value = router
        assert main(["llm", "complete", "--prompt", "Say OK.", "--task-class", "simple"]) == 0
    out = capsys.readouterr().out
    assert "OK" in out
    assert "qwen2.5-coder:7b" in out


def test_run_default_still_mock(workspace: Path, capsys) -> None:
    assert main(["init", "llm-demo"]) == 0
    assert main(["run", "llm-demo", "--llm", "mock", "--goal", "hello", "--steps", "2"]) == 0
    out = capsys.readouterr().out
    assert "cycle completed" in out or "task:" in out or "completed" in out
    hello = ws.project_root(workspace, "llm-demo") / ".forge" / "reports" / "hello.md"
    assert hello.exists()
