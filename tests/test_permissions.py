from forgeos.roles.loader import RolePolicy
from forgeos.safety.permissions import check


def _role(**kwargs) -> RolePolicy:
    base = dict(
        id="backend",
        name="Backend",
        purpose="t",
        writes=["backend/**"],
        allowed_tools=[
            "filesystem.write",
            "filesystem.delete",
            "git.commit",
            "docker.compose_up",
        ],
        forbidden=[],
        definition_of_done=["ok"],
        may_commit_feature_branch=True,
        requires_human_for_critical=True,
    )
    base.update(kwargs)
    return RolePolicy(**base)


def test_allow_low_risk_write() -> None:
    role = _role()
    d = check(role, {"tool": "filesystem.write", "path": "x"}, task_risk="low", branch="feature/x")
    assert d.kind == "allow"


def test_need_approval_critical_tool() -> None:
    role = _role()
    d = check(role, {"tool": "filesystem.delete", "path": "x"}, task_risk="low", branch="feature/x")
    assert d.kind == "need_approval"
    assert "filesystem.delete" in d.reason


def test_need_approval_high_risk() -> None:
    role = _role()
    d = check(role, {"tool": "filesystem.write", "path": "x"}, task_risk="critical", branch="feature/x")
    assert d.kind == "need_approval"


def test_need_approval_commit_on_main() -> None:
    role = _role(may_commit_feature_branch=True)
    d = check(role, {"tool": "git.commit", "message": "m"}, task_risk="low", branch="main")
    assert d.kind == "need_approval"


def test_need_approval_commit_without_flag() -> None:
    role = _role(may_commit_feature_branch=False)
    d = check(role, {"tool": "git.commit", "message": "m"}, task_risk="low", branch="feature/x")
    assert d.kind == "need_approval"


def test_allow_critical_when_human_not_required() -> None:
    role = _role(requires_human_for_critical=False)
    d = check(role, {"tool": "filesystem.delete", "path": "x"}, task_risk="low", branch="feature/x")
    assert d.kind == "allow"
    assert "without human gate" in d.reason


def test_deny_unknown_tool() -> None:
    role = _role()
    d = check(role, {"tool": "terminal.execute", "command": "echo"}, task_risk="low")
    assert d.kind == "deny"
