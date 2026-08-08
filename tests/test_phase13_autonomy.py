from forgeos.core.classifier import FailureClassifier
from forgeos.core import world_state as ws
from forgeos.llm.governor import ResourceGovernor, VramSnapshot
from forgeos.llm.model_router import ModelRouter
from forgeos.planning.replan import Replanner
from forgeos.planning.task_graph import Task, TaskGraph
from forgeos.planning.templates import (
    full_pipeline_full_template,
    is_full_pipeline_goal,
    select_template,
)
from forgeos.scaffold import scaffold_fastapi_health


def test_is_full_pipeline_goal() -> None:
    assert is_full_pipeline_goal("Run full pipeline autonomy from CEO to reporter")
    assert is_full_pipeline_goal("CEO and product manager with architect plan")
    assert not is_full_pipeline_goal("Create FastAPI /health endpoint")


def test_full_pipeline_template_roles() -> None:
    tasks = full_pipeline_full_template("autonomy goal")
    ids = [t.id for t in tasks]
    assert ids == [
        "ceo-001",
        "pm-001",
        "arch-001",
        "be-001",
        "qa-001",
        "doc-001",
        "ops-001",
        "rep-001",
    ]
    assert tasks[0].role == "ceo"
    assert tasks[1].role == "product_manager"
    assert tasks[2].role == "software_architect"
    assert tasks[-1].role == "reporter"


def test_select_full_pipeline_template(workspace) -> None:
    root = ws.create_project(workspace, "pipe")
    tasks = select_template("x", template="full-pipeline", project_root=root)
    assert tasks[0].id == "ceo-001"
    scaffold_fastapi_health(root)
    short = select_template("x", template="autonomy", project_root=root)
    assert short[0].id == "qa-001"
    assert any(t.id == "rep-001" for t in short)


def test_classify_uses_docker_daemon_stderr() -> None:
    msg = "exit=1\nCannot connect to the Docker daemon at unix:///var/run/docker.sock"
    result = FailureClassifier().classify(msg, tool="docker.compose_up", exit_code=1)
    assert result.failure_class == "env"


def test_replan_hard_class_blocks_without_fix() -> None:
    graph = TaskGraph()
    task = Task(
        id="ops-002",
        description="compose",
        status="RUNNING",
        role="devops",
        priority=10,
        action={"tool": "docker.compose_up"},
    )
    graph.add(task)
    r = Replanner().on_failure(
        graph,
        task,
        "Cannot connect to the Docker daemon",
        failure_class="env",
    )
    assert r.blocked
    assert r.fix_task is None
    assert task.status == "BLOCKED"
    assert not any(t.id.startswith("ops-002-fix") for t in graph.tasks)


def test_replan_nested_fix_blocks() -> None:
    graph = TaskGraph()
    task = Task(
        id="ops-002-fix-1",
        description="nested",
        status="RUNNING",
        role="devops",
        priority=10,
        action={"tool": "filesystem.write", "path": "x.md", "content": "x"},
    )
    graph.add(task)
    r = Replanner().on_failure(graph, task, "boom", failure_class="logic")
    assert r.blocked
    assert r.fix_task is None
    assert not any(t.id.endswith("-fix-1-fix-1") or "-fix-1-fix-" in t.id for t in graph.tasks)


def test_replan_soft_at_most_one_fix() -> None:
    graph = TaskGraph()
    task = Task(
        id="be-003",
        description="pytest",
        status="RUNNING",
        role="backend",
        priority=10,
        action={"tool": "testing.run"},
    )
    graph.add(task)
    r1 = Replanner(max_attempts=3).on_failure(graph, task, "assert fail", failure_class="logic")
    assert not r1.blocked
    assert r1.fix_task is not None
    assert r1.fix_task.id == "be-003-fix-1"
    r2 = Replanner(max_attempts=3).on_failure(graph, task, "assert fail again", failure_class="logic")
    assert r2.blocked
    assert r2.fix_task is None
    assert sum(1 for t in graph.tasks if "-fix-" in t.id) == 1


def test_governor_num_ctx_and_budget() -> None:
    gov = ResourceGovernor()
    assert gov.num_ctx_for("planning") == 2048
    assert gov.num_ctx_for("coding") == 4096
    assert gov.prompt_budget(vram=VramSnapshot(used_mib=10, total_mib=100)) == gov.default_budget
    assert gov.prompt_budget(vram=VramSnapshot(used_mib=90, total_mib=100)) == gov.pressure_budget


def test_governor_unload_llm(monkeypatch) -> None:
    class _Client:
        def __init__(self) -> None:
            self.unloaded: list[str] = []

        def unload(self, model: str) -> None:
            self.unloaded.append(model)

    class _Router:
        def __init__(self) -> None:
            self.client = _Client()
            self.current_model = "qwen2.5-coder:7b"

    class _LLM:
        def __init__(self) -> None:
            self.router = _Router()

    llm = _LLM()
    assert ResourceGovernor().unload_llm(llm) is True
    assert llm.router.client.unloaded == ["qwen2.5-coder:7b"]
    assert llm.router.current_model is None


def test_model_router_options_include_num_ctx() -> None:
    class _Client:
        def unload(self, model: str) -> None:
            return None

        def complete(self, prompt: str, *, model: str, options=None) -> str:
            return "ok"

    opts = ModelRouter(_Client()).options_for("planning")
    assert opts.get("num_ctx") == 2048
    assert opts.get("num_predict") == 768
