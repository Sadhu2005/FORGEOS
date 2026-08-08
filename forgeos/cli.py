"""FORGEOS CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forgeos import __version__
from forgeos.core import world_state as ws
from forgeos.core.executor import Executor
from forgeos.core.orchestrator import Orchestrator
from forgeos.llm.base import LLMClient, LLMError
from forgeos.llm.context_manager import ContextManager
from forgeos.llm.mock import MockLLM
from forgeos.llm.model_router import DEFAULT_ROUTING, ModelRouter, RoutedLLM
from forgeos.llm.ollama_client import OllamaClient, default_host
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
        llm, use_context = _build_llm(args.llm, task_class="planning")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    orch = Orchestrator(
        workspace,
        args.name,
        role_id=args.role,
        llm=llm,
        context=ContextManager(project_root=project),
        use_context=use_context,
    )
    try:
        result = orch.run_once(goal=goal)
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(result.message)
    print(f"task: {result.task_id}")
    if result.report_path:
        print(f"report: {result.report_path}")
    for item in result.evidence:
        print(f"  {item}")
    return 0 if result.ok else 1


def _tool_demo(workspace: Path, name: str, role_id: str) -> int:
    project = ws.project_root(workspace, name)
    # Default ceo lacks terminal/git; smoke uses backend unless caller overrides.
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
        print(f"reachable: false")
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

    p_run = sub.add_parser("run", help="run one PLAN-ACT-OBSERVE-VERIFY cycle")
    p_run.add_argument("name", help="project name")
    p_run.add_argument("--goal", default=None, help="goal text for the stub planner")
    p_run.add_argument("--role", default="ceo", help="role policy id (default: ceo)")
    p_run.add_argument(
        "--llm",
        choices=("mock", "ollama"),
        default="mock",
        help="LLM backend (default: mock)",
    )
    p_run.add_argument(
        "--tool-demo",
        action="store_true",
        help="smoke terminal.execute + git.status instead of stub planner cycle",
    )
    p_run.set_defaults(func=cmd_run)

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
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
