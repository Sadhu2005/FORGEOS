from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.roles.loader import RolePolicy, load_role
from forgeos.tools.registry import ToolRegistry, default_tool_ids


def test_default_tool_ids_complete() -> None:
    ids = default_tool_ids()
    assert "filesystem.read" in ids
    assert "terminal.execute" in ids
    assert "git.commit" in ids
    assert "testing.run" in ids
    assert "docker.compose_config" in ids


def test_registry_dispatch_and_unknown(workspace: Path) -> None:
    root = ws.create_project(workspace, "reg")
    role = load_role(workspace, "ceo")
    registry = ToolRegistry(root, role)
    assert "filesystem.tree" in registry.list_tools()

    ok = registry.dispatch({"tool": "filesystem.tree", "max_depth": 1})
    assert ok.ok

    denied = registry.dispatch({"tool": "terminal.execute", "command": "echo hi"})
    assert not denied.ok
    assert "not allowed" in denied.detail

    open_role = RolePolicy(
        id="open",
        name="Open",
        purpose="test",
        writes=["**"],
        allowed_tools=["no.such.tool", "filesystem.tree"],
        forbidden=[],
        definition_of_done=[],
        may_commit_feature_branch=False,
        requires_human_for_critical=True,
    )
    open_reg = ToolRegistry(root, open_role)
    unknown = open_reg.dispatch({"tool": "no.such.tool"})
    assert not unknown.ok
    assert "unknown tool" in unknown.detail
