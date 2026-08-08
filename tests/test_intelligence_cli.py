from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.intelligence.debt import debt_path
from forgeos.intelligence.health import health_path
from forgeos.llm.context_manager import ContextManager


def test_intelligence_cli(workspace: Path, capsys) -> None:
    assert main(["init", "intel-demo"]) == 0
    root = ws.project_root(workspace, "intel-demo")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("FORGEOS local health probe\n", encoding="utf-8")
    (root / "code.py").write_text("# TODO: later\n", encoding="utf-8")

    assert main(["intelligence", "health", "intel-demo"]) == 0
    out = capsys.readouterr().out
    assert "health:" in out
    assert health_path(root).is_file()

    assert main(["intelligence", "debt", "intel-demo"]) == 0
    out = capsys.readouterr().out
    assert "score=" in out
    assert debt_path(root).is_file()

    assert main(["intelligence", "research", "intel-demo", "--query", "health"]) == 0
    out = capsys.readouterr().out
    assert "note.md" in out or "health" in out.lower()

    prompt = ContextManager(project_root=root).build(
        goal="g",
        role_id="ceo",
        allowed_tools=[],
    )
    assert "## Health" in prompt
    assert "## Debt" in prompt
