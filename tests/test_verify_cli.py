from pathlib import Path

from forgeos.cli import main
from forgeos.core import world_state as ws


def test_classify_cli(workspace: Path, capsys) -> None:
    assert main(["classify", "--error", "ModuleNotFoundError: No module named x"]) == 0
    out = capsys.readouterr().out
    assert "class: dependency" in out


def test_verify_cli(workspace: Path, capsys) -> None:
    assert main(["init", "verify-demo"]) == 0
    assert main(["plan", "verify-demo", "--goal", "phase5", "--llm", "mock"]) == 0
    assert main(["run", "verify-demo", "--steps", "1", "--goal", "phase5"]) == 0
    assert main(["verify", "verify-demo", "--task", "task-001"]) == 0
    out = capsys.readouterr().out
    assert "status: PASS" in out
    evidence_files = list(
        (ws.project_root(workspace, "verify-demo") / ".forge" / "reports").glob("evidence-*.yaml")
    )
    assert evidence_files
