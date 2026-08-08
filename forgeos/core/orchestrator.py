"""Orchestrator: one PLAN → ACT → OBSERVE → VERIFY cycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.core.executor import Executor
from forgeos.core.observer import Observer
from forgeos.core.verifier import Verifier
from forgeos.llm.mock import MockLLM
from forgeos.planning.planner import PlannerStub
from forgeos.planning.task_graph import TaskGraph
from forgeos.roles.loader import RolePolicy, load_role
from forgeos.tools.filesystem import FilesystemTool


@dataclass
class CycleResult:
    ok: bool
    project: Path
    task_id: str
    report_path: Path | None
    evidence: list[str]
    message: str


class Orchestrator:
    def __init__(
        self,
        workspace: Path,
        project_name: str,
        role_id: str = "ceo",
        llm: MockLLM | None = None,
    ) -> None:
        self.workspace = workspace.resolve()
        self.project_name = project_name
        self.project = ws.project_root(self.workspace, project_name)
        self.role_id = role_id
        self.llm = llm or MockLLM()
        self._llm_guard = False

    def _with_llm_guard(self, fn):
        if self._llm_guard:
            raise RuntimeError("orchestrator: concurrent LLM use rejected")
        self._llm_guard = True
        try:
            return fn()
        finally:
            self._llm_guard = False

    def run_once(self, goal: str = "Phase 1 stub: write hello report") -> CycleResult:
        state = ws.load(self.project)
        graph = TaskGraph.load(ws.tasks_path(self.project))
        role = load_role(self.workspace, self.role_id)

        planner = PlannerStub(self.llm)

        def _plan():
            return planner.plan(goal, graph)

        task = self._with_llm_guard(_plan)
        task.status = "RUNNING"
        graph.save(ws.tasks_path(self.project))

        fs = FilesystemTool(self.project, role.writes)
        self._assert_tool_allowed(role, task.action.get("tool", ""))
        executor = Executor(fs, role)
        exec_result = executor.execute(task.action)
        if not exec_result.ok:
            task.status = "FAILED"
            graph.save(ws.tasks_path(self.project))
            report = self._write_report(goal, task.id, False, [exec_result.detail], role)
            return CycleResult(False, self.project, task.id, report, [exec_result.detail], exec_result.detail)

        observer = Observer(fs)
        rel_path = str(task.action.get("path", ""))
        observation = observer.observe_file(rel_path)

        task.status = "VERIFYING"
        verifier = Verifier()
        verify = verifier.verify(task, observation)
        task.evidence = list(verify.evidence)
        if verify.ok:
            task.status = "COMPLETED"
            task.artifacts = [rel_path]
            message = "cycle completed"
        else:
            task.status = "FAILED"
            message = "; ".join(verify.failures)

        counts = graph.update_counts()
        state["tasks"] = counts
        ws.save(self.project, state)
        graph.save(ws.tasks_path(self.project))

        report = self._write_report(goal, task.id, verify.ok, verify.evidence + verify.failures, role)
        return CycleResult(verify.ok, self.project, task.id, report, task.evidence, message)

    def _assert_tool_allowed(self, role: RolePolicy, tool: str) -> None:
        if tool and tool not in role.allowed_tools:
            raise PermissionError(f"role {role.id} cannot use tool {tool}")

    def _write_report(
        self,
        goal: str,
        task_id: str,
        ok: bool,
        evidence: list[str],
        role: RolePolicy,
    ) -> Path:
        reports = ws.reports_dir(self.project)
        reports.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = reports / f"task-{task_id}-{stamp}.md"
        status = "COMPLETED" if ok else "FAILED"
        lines = [
            "# TASK REPORT",
            "",
            f"Task: {task_id}",
            f"Goal: {goal}",
            f"Role: {role.id}",
            f"Status: {status}",
            f"Time: {stamp}",
            "",
            "## Evidence",
            "",
        ]
        lines.extend(f"- {item}" for item in evidence)
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
