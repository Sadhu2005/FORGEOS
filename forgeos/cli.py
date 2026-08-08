"""FORGEOS CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forgeos import __version__
from forgeos.core import world_state as ws
from forgeos.core.orchestrator import Orchestrator


def _workspace() -> Path:
    return Path.cwd()


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
    goal = args.goal or "Phase 1 stub: write hello report"
    orch = Orchestrator(workspace, args.name, role_id=args.role)
    result = orch.run_once(goal=goal)
    print(result.message)
    print(f"task: {result.task_id}")
    if result.report_path:
        print(f"report: {result.report_path}")
    for item in result.evidence:
        print(f"  {item}")
    return 0 if result.ok else 1


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
    p_run.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
