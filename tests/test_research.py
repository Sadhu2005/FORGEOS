from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.intelligence.research import search
from forgeos.roles.loader import load_role
from forgeos.tools.registry import ToolRegistry


def test_research_search_docs(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "res1")
    docs = root / "docs"
    docs.mkdir()
    (docs / "ARCHITECTURE.md").write_text("# Architecture\nUse PostgreSQL store.\n", encoding="utf-8")
    hits = search(root, "PostgreSQL", limit=5)
    assert hits
    assert hits[0]["path"].endswith("ARCHITECTURE.md")


def test_research_and_world_state_tools(workspace: Path) -> None:
    root = ws.create_project(workspace, "res-tools")
    (root / "docs").mkdir()
    (root / "docs" / "a.md").write_text("alpha beta gamma\n", encoding="utf-8")
    role = load_role(workspace, "software_architect")
    reg = ToolRegistry(root, role)
    r = reg.dispatch({"tool": "research", "query": "beta"})
    assert r.ok
    assert r.data and r.data["hits"]
    w = reg.dispatch({"tool": "world_state.read"})
    assert w.ok
    assert w.data["project"]["name"] == "res-tools"
