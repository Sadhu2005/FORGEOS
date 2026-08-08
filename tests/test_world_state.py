from pathlib import Path

from forgeos.core import world_state as ws


def test_create_and_load_world_state(workspace: Path) -> None:
    root = ws.create_project(workspace, "demo")
    assert ws.state_path(root).exists()
    state = ws.load(root)
    assert state["project"]["name"] == "demo"
    assert state["project"]["status"] == "active"
    assert "tasks" in state


def test_save_roundtrip(workspace: Path) -> None:
    root = ws.create_project(workspace, "round")
    state = ws.load(root)
    state["project"]["phase"] = "testing"
    ws.save(root, state)
    again = ws.load(root)
    assert again["project"]["phase"] == "testing"


def test_missing_required_key_rejected(workspace: Path) -> None:
    root = ws.create_project(workspace, "bad")
    try:
        ws.save(root, {"project": {"name": "x"}})
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "missing" in str(exc)
