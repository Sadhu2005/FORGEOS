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
from forgeos.memory.database import memory_path
from forgeos.memory.repository import Repository
from forgeos.planning.task_graph import TaskGraph
from forgeos.roles.loader import load_role
from forgeos.safety.approval import ApprovalStore
from forgeos.safety.audit import AuditLog
from forgeos.tools.git import GitTool
from forgeos.tools.registry import default_tool_ids
from forgeos.intelligence.debt import debt_path, scan as debt_scan
from forgeos.intelligence.health import health_path, probe as health_probe
from forgeos.intelligence.research import search as research_search
from forgeos.dashboard.server import DEFAULT_HOST, DEFAULT_PORT, serve as serve_dashboard


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
    with_db = bool(getattr(args, "with_db", False))
    with_frontend = bool(getattr(args, "with_frontend", False))
    do_scaffold = (
        bool(getattr(args, "scaffold", False)) or with_db or with_frontend
    )
    try:
        root = ws.create_project(workspace, args.name)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if do_scaffold:
        from forgeos.scaffold import scaffold_fastapi_health

        written = scaffold_fastapi_health(
            root,
            name=args.name,
            with_db=with_db,
            with_frontend=with_frontend,
        )
        extras: list[str] = []
        if with_db:
            extras.append("Postgres profile")
        if with_frontend:
            extras.append("Next.js frontend")
        extra = f" + {' + '.join(extras)}" if extras else ""
        print(f"scaffolded FastAPI /health tree{extra} ({len(written)} files)")
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
        template = getattr(args, "template", None)
        if template:
            orch.plan_template = template
        graph = orch.ensure_plan(goal, force=bool(args.force), template=template)
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


def cmd_memory_status(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    repo = Repository(project)
    if not repo.db_path.exists():
        try:
            repo.sync_from_yaml()
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    counts = repo.counts()
    print(f"db: {memory_path(project)}")
    print(f"project_meta: {counts['project_meta']}")
    print(f"tasks: {counts['tasks']}")
    print(f"decisions: {counts['decisions']}")
    print(f"events: {counts['events']}")
    return 0


def cmd_memory_decisions(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    repo = Repository(project)
    if not repo.db_path.exists():
        print("(no memory database; run: forgeos memory sync <project>)")
        return 0
    decisions = repo.list_decisions(limit=int(args.limit))
    if not decisions:
        print("(no decisions)")
        return 0
    for d in decisions:
        print(
            f"{d.get('id')}\t{d.get('timestamp')}\tchosen={d.get('chosen')}\t"
            f"confidence={d.get('confidence')}\t{d.get('problem')}"
        )
    return 0


def cmd_memory_sync(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    repo = Repository(project)
    try:
        repo.sync_from_yaml()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    counts = repo.counts()
    print(f"synced: {memory_path(project)}")
    print(
        f"tasks={counts['tasks']} decisions={counts['decisions']} events={counts['events']}"
    )
    return 0


def _unblock_task(project: Path, task_id: str) -> None:
    graph = TaskGraph.load(ws.tasks_path(project))
    task = graph.get(task_id)
    if task is not None and task.status == "BLOCKED":
        task.status = "READY"
        task.last_error = ""
        graph.save(ws.tasks_path(project))


def cmd_safety_pending(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    pending = ApprovalStore(project).list_pending()
    if not pending:
        print("(no pending approvals)")
        return 0
    for ticket in pending:
        print(
            f"{ticket.get('id')}\ttask={ticket.get('task_id')}\t"
            f"tool={ticket.get('tool')}\trisk={ticket.get('risk')}\t{ticket.get('reason')}"
        )
    return 0


def cmd_safety_approve(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    store = ApprovalStore(project)
    try:
        ticket = store.approve(args.id)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _unblock_task(project, str(ticket.get("task_id") or ""))
    AuditLog(project).append(
        "approval",
        f"approved {ticket['id']}",
        task_id=str(ticket.get("task_id") or ""),
        payload={"approval_id": ticket["id"], "status": "approved"},
    )
    print(f"approved: {ticket['id']}")
    print(f"task: {ticket.get('task_id')} -> READY")
    return 0


def cmd_safety_reject(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    store = ApprovalStore(project)
    try:
        ticket = store.reject(args.id)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    AuditLog(project).append(
        "approval",
        f"rejected {ticket['id']}",
        task_id=str(ticket.get("task_id") or ""),
        payload={"approval_id": ticket["id"], "status": "rejected"},
    )
    print(f"rejected: {ticket['id']}")
    return 0


def cmd_safety_audit(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    log = AuditLog(project)
    rows = log.read_lines(limit=int(args.limit))
    if not rows:
        print("(no audit entries)")
        return 0
    print(f"audit: {log.path}")
    for row in rows:
        print(
            f"{row.get('timestamp')}\t{row.get('kind')}\t"
            f"task={row.get('task_id') or '-'}\t{row.get('message')}"
        )
    return 0


def cmd_checkpoint_create(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    result = GitTool(project).checkpoint(message=args.message or "")
    AuditLog(project).append(
        "checkpoint",
        result.detail,
        payload=dict(result.data or {}),
    )
    print(f"checkpoint: {result.detail}")
    if result.path:
        print(f"path: {result.path}")
    return 0 if result.ok else 1


def cmd_checkpoint_list(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    entries = GitTool(project).list_checkpoints()
    if not entries:
        print("(no checkpoints)")
        return 0
    for entry in entries:
        print(
            f"{entry.get('id')}\tsha={entry.get('sha') or '-'}\t"
            f"tag={entry.get('tag') or '-'}\t{entry.get('message')}"
        )
    return 0


def cmd_intelligence_health(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    report = health_probe(project)
    tests = report.get("tests") or {}
    env = report.get("environment") or {}
    print(f"health: {health_path(project)}")
    print(
        f"tests: total={tests.get('total', 0)} passing={tests.get('passing', 0)} "
        f"failing={tests.get('failing', 0)}"
    )
    print(
        f"env: python={env.get('python')} docker={env.get('docker')} "
        f"compose_ok={env.get('compose_config_ok')}"
    )
    for note in report.get("notes") or []:
        print(f"note: {note}")
    return 0


def cmd_intelligence_debt(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    report = debt_scan(project)
    print(f"debt: {debt_path(project)}")
    print(
        f"score={report.get('score')} todo={report.get('todo_count')} "
        f"fixme={report.get('fixme_count')} blocked={report.get('blocked_tasks')} "
        f"approvals={report.get('pending_approvals')} failing_tests={report.get('failing_tests')}"
    )
    for hit in (report.get("top_hits") or [])[:10]:
        print(f"  {hit.get('path')}:{hit.get('line')} {hit.get('text')}")
    return 0


def cmd_intelligence_research(args: argparse.Namespace) -> int:
    workspace = _workspace()
    project = ws.project_root(workspace, args.name)
    if not ws.state_path(project).exists():
        print(f"error: project not found; run: forgeos init {args.name}", file=sys.stderr)
        return 1
    hits = research_search(project, args.query, limit=int(args.limit))
    if not hits:
        print("(no hits)")
        return 0
    for hit in hits:
        print(f"{hit.get('path')}:{hit.get('line')}\t{hit.get('text')}")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    host = args.host
    if host not in ("127.0.0.1", "localhost", "::1") and not args.allow_remote:
        print(
            f"error: refusing to bind {host!r}; use 127.0.0.1 or pass --allow-remote",
            file=sys.stderr,
        )
        return 1
    try:
        serve_dashboard(
            _workspace(),
            host=host,
            port=int(args.port),
            allow_remote=bool(args.allow_remote),
        )
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
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
    p_init.add_argument(
        "--scaffold",
        action="store_true",
        help="also write minimal FastAPI /health + docker + docs tree",
    )
    p_init.add_argument(
        "--with-db",
        action="store_true",
        help="with scaffold: write .env.example and Postgres profile docs (implies --scaffold)",
    )
    p_init.add_argument(
        "--with-frontend",
        action="store_true",
        help="with scaffold: write Next.js frontend + compose frontend service (implies --scaffold)",
    )
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
    p_plan.add_argument(
        "--template",
        choices=(
            "fastapi-health",
            "fastapi-next-health",
            "full-pipeline",
            "default",
        ),
        default=None,
        help="seed graph template (default: auto-detect from goal)",
    )
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

    p_memory = sub.add_parser("memory", help="inspect project SQLite memory")
    memory_sub = p_memory.add_subparsers(dest="memory_command")

    p_mem_status = memory_sub.add_parser("status", help="show sqlite path and row counts")
    p_mem_status.add_argument("name", help="project name")
    p_mem_status.set_defaults(func=cmd_memory_status)

    p_mem_decisions = memory_sub.add_parser("decisions", help="list recent decisions")
    p_mem_decisions.add_argument("name", help="project name")
    p_mem_decisions.add_argument("--limit", type=int, default=20, help="max rows (default: 20)")
    p_mem_decisions.set_defaults(func=cmd_memory_decisions)

    p_mem_sync = memory_sub.add_parser("sync", help="force YAML → SQLite sync")
    p_mem_sync.add_argument("name", help="project name")
    p_mem_sync.set_defaults(func=cmd_memory_sync)

    p_safety = sub.add_parser("safety", help="approvals and audit")
    safety_sub = p_safety.add_subparsers(dest="safety_command")

    p_safety_pending = safety_sub.add_parser("pending", help="list pending approvals")
    p_safety_pending.add_argument("name", help="project name")
    p_safety_pending.set_defaults(func=cmd_safety_pending)

    p_safety_approve = safety_sub.add_parser("approve", help="approve a pending ticket")
    p_safety_approve.add_argument("name", help="project name")
    p_safety_approve.add_argument("--id", required=True, help="approval id")
    p_safety_approve.set_defaults(func=cmd_safety_approve)

    p_safety_reject = safety_sub.add_parser("reject", help="reject a pending ticket")
    p_safety_reject.add_argument("name", help="project name")
    p_safety_reject.add_argument("--id", required=True, help="approval id")
    p_safety_reject.set_defaults(func=cmd_safety_reject)

    p_safety_audit = safety_sub.add_parser("audit", help="show recent audit JSONL entries")
    p_safety_audit.add_argument("name", help="project name")
    p_safety_audit.add_argument("--limit", type=int, default=50, help="max rows (default: 50)")
    p_safety_audit.set_defaults(func=cmd_safety_audit)

    p_checkpoint = sub.add_parser("checkpoint", help="git safety checkpoints")
    checkpoint_sub = p_checkpoint.add_subparsers(dest="checkpoint_command")

    p_ckpt_create = checkpoint_sub.add_parser("create", help="record HEAD checkpoint")
    p_ckpt_create.add_argument("name", help="project name")
    p_ckpt_create.add_argument("--message", default="", help="checkpoint message")
    p_ckpt_create.set_defaults(func=cmd_checkpoint_create)

    p_ckpt_list = checkpoint_sub.add_parser("list", help="list recorded checkpoints")
    p_ckpt_list.add_argument("name", help="project name")
    p_ckpt_list.set_defaults(func=cmd_checkpoint_list)

    p_intel = sub.add_parser("intelligence", help="health, debt, and local research")
    intel_sub = p_intel.add_subparsers(dest="intelligence_command")

    p_intel_health = intel_sub.add_parser("health", help="probe tests/env/compose")
    p_intel_health.add_argument("name", help="project name")
    p_intel_health.set_defaults(func=cmd_intelligence_health)

    p_intel_debt = intel_sub.add_parser("debt", help="scan TODO/blocked/approvals debt")
    p_intel_debt.add_argument("name", help="project name")
    p_intel_debt.set_defaults(func=cmd_intelligence_debt)

    p_intel_research = intel_sub.add_parser("research", help="search local docs/reports")
    p_intel_research.add_argument("name", help="project name")
    p_intel_research.add_argument("--query", required=True, help="search text")
    p_intel_research.add_argument("--limit", type=int, default=10, help="max hits (default: 10)")
    p_intel_research.set_defaults(func=cmd_intelligence_research)

    p_dash = sub.add_parser("dashboard", help="serve local engine dashboard")
    p_dash.add_argument("--host", default=DEFAULT_HOST, help=f"bind host (default: {DEFAULT_HOST})")
    p_dash.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port (default: {DEFAULT_PORT})")
    p_dash.add_argument(
        "--allow-remote",
        action="store_true",
        help="allow non-loopback bind (explicit opt-in)",
    )
    p_dash.set_defaults(func=cmd_dashboard)

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
    if args.command == "memory" and not getattr(args, "memory_command", None):
        parser.parse_args(["memory", "--help"])
        return 0
    if args.command == "safety" and not getattr(args, "safety_command", None):
        parser.parse_args(["safety", "--help"])
        return 0
    if args.command == "checkpoint" and not getattr(args, "checkpoint_command", None):
        parser.parse_args(["checkpoint", "--help"])
        return 0
    if args.command == "intelligence" and not getattr(args, "intelligence_command", None):
        parser.parse_args(["intelligence", "--help"])
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
