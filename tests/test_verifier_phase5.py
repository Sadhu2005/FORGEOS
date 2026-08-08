from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.core.observer import Observation
from forgeos.core.verifier import Verifier
from forgeos.planning.task_graph import Task
from forgeos.roles.loader import load_role
from forgeos.tools.filesystem import FilesystemTool


def test_contains_and_exists(workspace: Path) -> None:
    root = ws.create_project(workspace, "ver")
    role = load_role(workspace, "ceo")
    fs = FilesystemTool(root, role.writes)
    fs.write(".forge/reports/note.md", "hello forgeos phase5")
    task = Task(
        id="t1",
        description="check",
        status="VERIFYING",
        role="ceo",
        verification=["file exists", "file is non-empty", "contains:forgeos"],
        action={"tool": "filesystem.write", "path": ".forge/reports/note.md"},
    )
    obs = Observation(
        path=".forge/reports/note.md",
        exists=True,
        size=20,
        notes=[],
        content="hello forgeos phase5",
    )
    result = Verifier().verify(task, obs)
    assert result.ok
    assert result.bundle is not None
    path = result.bundle.write_yaml(ws.reports_dir(root))
    assert path.exists()


def test_exit_code_check() -> None:
    task = Task(
        id="t2",
        description="exit",
        status="VERIFYING",
        role="ceo",
        verification=["exit_code:0"],
        action={"tool": "terminal.execute"},
    )
    obs = Observation(path="", exists=True, size=0, notes=[], exit_code=0)
    assert Verifier().verify(task, obs).ok
    obs_bad = Observation(path="", exists=False, size=0, notes=[], exit_code=1)
    assert not Verifier().verify(task, obs_bad).ok
