from pathlib import Path

import pytest

from forgeos.roles.loader import list_roles, load_role, validate_role_dict


def test_load_ceo(workspace: Path) -> None:
    role = load_role(workspace, "ceo")
    assert role.id == "ceo"
    assert "filesystem.write" in role.allowed_tools
    assert role.writes


def test_list_roles(workspace: Path) -> None:
    roles = list_roles(workspace)
    assert "ceo" in roles
    assert "frontend" in roles
    assert len(roles) >= 11


def test_validate_missing_field() -> None:
    with pytest.raises(ValueError, match="missing required field"):
        validate_role_dict({"id": "x"})
