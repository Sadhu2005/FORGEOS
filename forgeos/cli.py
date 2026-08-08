"""FORGEOS CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forgeos import __version__
from forgeos.core import world_state as ws
from forgeos.core.classifier import FailureClassifier
from forgeos.core.executor import Executor
from forgeos.core.observer import Observer
from forgeos.core.orchestrator import Orchestrator
from forgeos.core.verifier import Verifier
from forgeos.llm.base import LLMClient, LLMError
from forgeos.llm.context_manager import ContextManager
from forgeos.llm.mock import MockLLM
from forgeos.llm.model_router import DEFAULT_ROUTING, ModelRouter, RoutedLLM
from forgeos.llm.ollama_client import OllamaClient, default_host
from forgeos.planning.task_graph import TaskGraph
from forgeos.roles.loader import load_role
from forgeos.tools.registry import default_tool_ids


def _workspace() -> Path:
    return Path.cwd()


def _build_llm(kind: str, task_class: str = "planning") -> tuple[LLMClient, bool]:
    """Return (client, use_context)."""
    if kind == "mock":
        return MockLLM(), False
    if kind == "ollama":
        client = OllamaClient()
        router = ModelRouter(client)
        return RoutedLLM(router, task_class=task_class), True
    raise ValueError(f"unknown llm backend: {kind}")


def _make_orch(workspace: Path, name: str, args: argparse.Namespace) -> Orchestrator:
    llm, use_context = _build_llm(args.llm, task_class="planning")
    project = ws.project_root(workspace, name)
    return Orchestrator(
        workspace,
        name,
        role_id=getattr(args, "role", "ceo"),
        llm=llm,
        context=ContextManager(project_root=project),
        use_context=use_context,
    )


def cmd_init(args: argparse.Namespace) -> int:
    workspace = _workspace()
    try:
        root = ws.create_project(workspace, args.name)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"initialized project at {root}")
    print(f"state: {ws.state_path(root)}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    try:
        state = ws.load(project)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    proj = state["project"]
    tasks = state.get("tasks", {})
    print(f"project: {proj.get('name')}")
    print(f"phase:   {proj.get('phase')}")
    print(f"status:  {proj.get('status')}")
    print(
        f"tasks:   completed={tasks.get('completed', 0)} "
        f"pending={tasks.get('pending', 0)} blocked={tasks.get('blocked', 0)}"
    )
    print(f"path:    {project}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1

    if args.tool_demo:
        return _tool_demo(workspace, args.name, args.role)

    goal = args.goal or "Phase 1 stub: write hello report"
    try:
        orch = _make_orch(workspace, args.name, args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    try:
        steps = int(args.steps)
        if steps <= 1:
            result = orch.run_once(goal=goal)
            print(result.message)
            print(f"task: {result.task_id}")
            if result.report_path:
                print(f"report: {result.report_path}")
            for item in result.evidence:
                print(f"  {item}")
            return 0 if result.ok else 1
        batch = orch.run_steps(goal=goal, steps=steps)
        print(batch.message)
        for cycle in batch.cycles:
            print(f"- {cycle.task_id or '(none)'}: {cycle.message} ok={cycle.ok}")
        return 0 if batch.ok else 1
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_plan(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    goal = args.goal or "Phase 4 plan"
    try:
        orch = _make_orch(workspace, args.name, args)
        graph = orch.ensure_plan(goal, force=bool(args.force))
    except (ValueError, LLMError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"goal: {goal}")
    print(f"tasks: {len(graph.tasks)}")
    for task in graph.tasks:
        deps = ",".join(task.dependencies) if task.dependencies else "-"
        print(f"  {task.id}\t{task.status}\trole={task.role}\tpri={task.priority}\tdeps={deps}")
    return 0


def cmd_tasks_list(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    graph = TaskGraph.load(ws.tasks_path(project))
    if not graph.tasks:
        print("(no tasks)")
        return 0
    for task in graph.tasks:
        deps = ",".join(task.dependencies) if task.dependencies else "-"
        print(
            f"{task.id}\t{task.status}\trole={task.role}\t"
            f"pri={task.priority}\tdeps={deps}\tattempts={task.attempts}"
        )
    return 0


def _tool_demo(workspace: Path, name: str, role_id: str) -> int:
    project = ws.project_root(workspace, name)
    if role_id == "ceo":
        role_id = "backend"
    role = load_role(workspace, role_id)
    executor = Executor(project, role)
    echo = executor.execute({"tool": "terminal.execute", "command": "echo forgeos-tool-demo"})
    print(f"terminal: ok={echo.ok} {echo.detail}")
    if echo.stdout.strip():
        print(echo.stdout.strip())
    status = executor.execute({"tool": "git.status"})
    print(f"git.status: ok={status.ok} {status.detail}")
    if status.stdout.strip():
        print(status.stdout.strip())
    return 0 if echo.ok and status.ok else 1


def cmd_tools_list(_args: argparse.Namespace) -> int:
    for tool_id in default_tool_ids():
        print(tool_id)
    return 0


def cmd_tools_exec(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    role = load_role(workspace, args.role)
    action: dict = {"tool": args.tool}
    for item in args.arg or []:
        if "=" not in item:
            print(f"error: bad --arg {item!r}, expected key=value", file=sys.stderr)
            return 1
        key, value = item.split("=", 1)
        if value.startswith("{") or value.startswith("["):
            try:
                action[key] = json.loads(value)
            except json.JSONDecodeError:
                action[key] = value
        else:
            action[key] = value
    result = Executor(project, role).execute(action)
    print(f"ok={result.ok} tool={result.tool} detail={result.detail}")
    if result.path:
        print(f"path={result.path}")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return 0 if result.ok else 1


def cmd_llm_status(_args: argparse.Namespace) -> int:
    host = default_host()
    print(f"host: {host}")
    print("routing defaults:")
    for task_class, model in DEFAULT_ROUTING.items():
        print(f"  {task_class}: {model}")
    client = OllamaClient(host=host)
    try:
        models = client.list_models()
    except LLMError as exc:
        print("reachable: false")
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("reachable: true")
    print("models:")
    for name in models:
        print(f"  {name}")
    return 0


def cmd_llm_complete(args: argparse.Namespace) -> int:
    client = OllamaClient()
    router = ModelRouter(client)
    try:
        text = router.complete(args.prompt, task_class=args.task_class)
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"model: {router.current_model}")
    print(text)
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    result = FailureClassifier().classify(
        args.error,
        tool=args.tool,
        exit_code=args.exit_code,
    )
    print(f"class: {result.failure_class}")
    print(f"confidence: {result.confidence}")
    print(f"reason: {result.reason}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    graph = TaskGraph.load(ws.tasks_path(project))
    task = graph.get(args.task)
    if task is None:
        print(f"error: task not found: {args.task}", file=sys.stderr)
        return 1
    role = load_role(workspace, task.role or "ceo")
    fs = Executor(project, role).fs
    observer = Observer(fs)
    rel_path = str(task.action.get("path", ""))
    observation = observer.observe_file(rel_path) if rel_path else observer.observe_file("")
    verify = Verifier().verify(task, observation)
    status = "PASS" if verify.ok else "FAIL"
    print(f"task: {task.id}")
    print(f"status: {status}")
    for item in verify.evidence:
        print(f"  {item}")
    for item in verify.failures:
        print(f"  {item}")
    if verify.bundle:
        path = verify.bundle.write_yaml(ws.reports_dir(project))
        print(f"evidence: {path}")
    return 0 if verify.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forgeos",
        description="FORGEOS — Local AI Engineering Operating System",
    )
    parser.add_argument("--version", action="version", version=f"forgeos {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="create a managed project sandbox")
    p_init.add_argument("name", help="project name under projects/")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="show world state summary")
    p_status.add_argument("name", help="project name")
    p_status.set_defaults(func=cmd_status)

    p_run = sub.add_parser("run", help="run PLAN-ACT-OBSERVE-VERIFY cycle(s)")
    p_run.add_argument("name", help="project name")
    p_run.add_argument("--goal", default=None, help="goal text for the planner")
    p_run.add_argument("--role", default="ceo", help="fallback role id (default: ceo)")
    p_run.add_argument(
        "--llm",
        choices=("mock", "ollama"),
        default="mock",
        help="LLM backend (default: mock)",
    )
    p_run.add_argument("--steps", type=int, default=1, help="max schedule cycles (default: 1)")
    p_run.add_argument(
        "--tool-demo",
        action="store_true",
        help="smoke terminal.execute + git.status instead of planner cycle",
    )
    p_run.set_defaults(func=cmd_run)

    p_plan = sub.add_parser("plan", help="build or refresh the task graph")
    p_plan.add_argument("name", help="project name")
    p_plan.add_argument("--goal", default=None, help="goal text")
    p_plan.add_argument("--role", default="ceo", help="role used for context")
    p_plan.add_argument("--llm", choices=("mock", "ollama"), default="mock")
    p_plan.add_argument("--force", action="store_true", help="replace existing graph")
    p_plan.set_defaults(func=cmd_plan)

    p_tasks = sub.add_parser("tasks", help="inspect task graph")
    tasks_sub = p_tasks.add_subparsers(dest="tasks_command")
    p_tasks_list = tasks_sub.add_parser("list", help="list tasks")
    p_tasks_list.add_argument("name", help="project name")
    p_tasks_list.set_defaults(func=cmd_tasks_list)

    p_tools = sub.add_parser("tools", help="inspect and execute tools")
    tools_sub = p_tools.add_subparsers(dest="tools_command")

    p_list = tools_sub.add_parser("list", help="list registered tool ids")
    p_list.set_defaults(func=cmd_tools_list)

    p_exec = tools_sub.add_parser("exec", help="execute one tool against a project")
    p_exec.add_argument("name", help="project name")
    p_exec.add_argument("--tool", required=True, help="tool id e.g. git.status")
    p_exec.add_argument("--role", default="ceo", help="role policy id")
    p_exec.add_argument(
        "--arg",
        action="append",
        default=[],
        help="action argument key=value (repeatable)",
    )
    p_exec.set_defaults(func=cmd_tools_exec)

    p_llm = sub.add_parser("llm", help="inspect and smoke-test local LLM")
    llm_sub = p_llm.add_subparsers(dest="llm_command")

    p_llm_status = llm_sub.add_parser("status", help="ping Ollama and list models")
    p_llm_status.set_defaults(func=cmd_llm_status)

    p_llm_complete = llm_sub.add_parser("complete", help="run one routed completion")
    p_llm_complete.add_argument("--prompt", required=True, help="prompt text")
    p_llm_complete.add_argument(
        "--task-class",
        choices=("coding", "simple", "planning"),
        default="simple",
        help="routing task class (default: simple)",
    )
    p_llm_complete.set_defaults(func=cmd_llm_complete)

    p_classify = sub.add_parser("classify", help="classify a failure message")
    p_classify.add_argument("--error", required=True, help="error / failure text")
    p_classify.add_argument("--tool", default=None, help="optional tool id")
    p_classify.add_argument("--exit-code", type=int, default=None, dest="exit_code")
    p_classify.set_defaults(func=cmd_classify)

    p_verify = sub.add_parser("verify", help="re-verify a task DoD against the project")
    p_verify.add_argument("name", help="project name")
    p_verify.add_argument("--task", required=True, help="task id")
    p_verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    if args.command == "tools" and not getattr(args, "tools_command", None):
        parser.parse_args(["tools", "--help"])
        return 0
    if args.command == "llm" and not getattr(args, "llm_command", None):
        parser.parse_args(["llm", "--help"])
        return 0
    if args.command == "tasks" and not getattr(args, "tasks_command", None):
        parser.parse_args(["tasks", "--help"])
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
