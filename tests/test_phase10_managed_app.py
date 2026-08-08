from pathlib import Path
from unittest.mock import MagicMock, patch

from forgeos.cli import main
from forgeos.core import world_state as ws
from forgeos.core.orchestrator import Orchestrator
from forgeos.core.observer import Observation
from forgeos.core.verifier import Verifier
from forgeos.llm.mock import MockLLM
from forgeos.planning.task_graph import Task
from forgeos.safety.approval import ApprovalStore
from forgeos.scaffold import scaffold_fastapi_health
from forgeos.tools.base import ToolResult
from forgeos.tools.docker import DockerTool


def test_cli_init_scaffold(workspace: Path, capsys) -> None:
    assert main(["init", "demo-scaf", "--scaffold"]) == 0
    out = capsys.readouterr().out
    assert "scaffolded" in out.lower()
    root = ws.project_root(workspace, "demo-scaf")
    assert (root / "backend" / "app" / "main.py").is_file()


def test_cli_plan_template_fastapi(workspace: Path, capsys) -> None:
    assert main(["init", "plan-fa"]) == 0
    assert (
        main(
            [
                "plan",
                "plan-fa",
                "--goal",
                "Create FastAPI /health endpoint",
                "--template",
                "fastapi-health",
                "--force",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "arch-001" in out
    assert "be-001" in out


def test_compose_up_real_by_default(workspace: Path) -> None:
    root = ws.create_project(workspace, "up1")
    compose = root / "docker" / "docker-compose.yml"
    compose.parent.mkdir(parents=True)
    compose.write_text("services:\n  web:\n    image: nginx\n", encoding="utf-8")
    tool = DockerTool(root)
    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = "Started"
    fake.stderr = ""
    with (
        patch("forgeos.tools.docker.shutil.which", return_value="docker"),
        patch("forgeos.tools.docker.subprocess.run", return_value=fake) as run,
    ):
        result = tool.compose_up("docker/docker-compose.yml")
    assert result.ok
    args = run.call_args[0][0]
    assert "up" in args and "-d" in args
    assert "--dry-run" not in args


def test_compose_up_dry_run_flag(workspace: Path) -> None:
    root = ws.create_project(workspace, "up2")
    compose = root / "docker" / "docker-compose.yml"
    compose.parent.mkdir(parents=True)
    compose.write_text("services:\n  web:\n    image: nginx\n", encoding="utf-8")
    tool = DockerTool(root)
    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = "Dry run"
    fake.stderr = ""
    with (
        patch("forgeos.tools.docker.shutil.which", return_value="docker"),
        patch("forgeos.tools.docker.subprocess.run", return_value=fake) as run,
    ):
        result = tool.compose_up("docker/docker-compose.yml", dry_run=True)
    assert result.ok
    assert "dry-run" in result.detail
    args = run.call_args[0][0]
    assert "--dry-run" in args


def test_verifier_pytest_pass() -> None:
    task = Task(
        id="t1",
        description="pytest",
        status="READY",
        role="backend",
        verification=["pytest_pass", "exit_code:0"],
        action={"tool": "testing.run"},
    )
    obs = Observation(path="", exists=True, size=0, notes=[], exit_code=0, stdout="1 passed")
    result = Verifier().verify(task, obs)
    assert result.ok
    assert result.checks["pytest_pass"]


def test_verifier_http_get_mocked() -> None:
    task = Task(
        id="t2",
        description="http",
        status="READY",
        role="qa",
        verification=["http_get:/health"],
        action={"tool": "filesystem.read", "path": "README.md"},
    )
    obs = Observation(path="README.md", exists=True, size=1, notes=["ok"], content="x")
    with patch("forgeos.core.verifier._http_get_ok", return_value=True):
        result = Verifier().verify(task, obs)
    assert result.ok
    assert result.checks["http_get:/health"]


def test_e2e_fastapi_mock_through_be003(workspace: Path) -> None:
    root = ws.create_project(workspace, "e2e-fa")
    goal = "Create a Python FastAPI project with a /health endpoint and tests"
    orch = Orchestrator(workspace, "e2e-fa", role_id="ceo", llm=MockLLM())
    orch.ensure_plan(goal, force=True, template="fastapi-health")

    def fake_testing_run(action):
        return ToolResult(True, "testing.run", "exit=0", exit_code=0, stdout="1 passed")

    with patch("forgeos.tools.registry.ToolRegistry._testing_run", side_effect=fake_testing_run):
        for _ in range(4):
            result = orch.run_once(goal)
            assert result.ok, result.message
            if result.task_id == "be-003":
                break
        else:
            raise AssertionError("be-003 never ran")
    assert (root / "backend" / "app" / "main.py").is_file()
    assert (root / "backend" / "tests" / "test_health.py").is_file()


def test_e2e_compose_up_approval_dry_run(workspace: Path) -> None:
    root = ws.create_project(workspace, "e2e-up")
    scaffold_fastapi_health(root)
    goal = "Create a Python FastAPI project with a /health endpoint and tests"
    orch = Orchestrator(workspace, "e2e-up", role_id="ceo", llm=MockLLM())
    orch.ensure_plan(goal, force=True, template="fastapi-health")
    # Short graph: be-003 → ops-001 → ops-002
    graph_path = ws.tasks_path(root)

    def fake_testing_run(action):
        return ToolResult(True, "testing.run", "exit=0", exit_code=0, stdout="1 passed")

    with patch("forgeos.tools.registry.ToolRegistry._testing_run", side_effect=fake_testing_run):
        r1 = orch.run_once(goal)
        assert r1.ok and r1.task_id == "be-003"
        r2 = orch.run_once(goal)
        assert r2.ok and r2.task_id == "ops-001"

    blocked = orch.run_once(goal)
    assert not blocked.ok
    assert "approval" in blocked.message.lower() or blocked.failure_class == "permission"
    pending = ApprovalStore(root).list_pending()
    assert pending
    ticket_id = pending[0]["id"]
    assert main(["safety", "approve", "e2e-up", "--id", ticket_id]) == 0

    fake_up = MagicMock(
        return_value=ToolResult(True, "docker.compose_up", "dry-run ok", exit_code=0)
    )
    with patch("forgeos.tools.registry.ToolRegistry._docker_compose_up", fake_up):
        # Force dry_run on the queued action for safety in tests
        from forgeos.planning.task_graph import TaskGraph

        graph = TaskGraph.load(graph_path)
        ops = graph.get("ops-002")
        assert ops is not None
        ops.action["dry_run"] = True
        graph.save(graph_path)
        done = orch.run_once(goal)
    assert done.ok
    assert done.task_id == "ops-002"
    fake_up.assert_called_once()
