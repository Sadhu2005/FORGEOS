from pathlib import Path

from forgeos.llm.context_manager import ContextManager


def test_build_basic() -> None:
    ctx = ContextManager(budget=8000)
    prompt = ctx.build(
        goal="ship phase3",
        role_id="ceo",
        allowed_tools=["filesystem.read", "filesystem.write"],
    )
    assert "Role: ceo" in prompt
    assert "Goal: ship phase3" in prompt
    assert "filesystem.write" in prompt


def test_truncate_over_budget(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    big = root / "big.txt"
    big.write_text("A" * 5000, encoding="utf-8")
    ctx = ContextManager(budget=200, project_root=root)
    prompt = ctx.build(
        goal="g",
        role_id="ceo",
        allowed_tools=[],
        file_paths=["big.txt"],
    )
    assert len(prompt) <= 220
    assert "truncated" in prompt or len(prompt) <= 200
