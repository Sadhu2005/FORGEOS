from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporary workspace with roles/ copied from repo and empty projects/."""
    import shutil

    repo = Path(__file__).resolve().parents[1]
    roles_src = repo / "roles"
    roles_dst = tmp_path / "roles"
    shutil.copytree(roles_src, roles_dst)
    (tmp_path / "projects").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path
