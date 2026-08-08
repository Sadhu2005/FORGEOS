"""Orchestrator: PLAN → schedule → ACT → OBSERVE → VERIFY (+ classify/replan)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from forgeos.core import world_state as ws
from forgeos.core.classifier import FailureClassifier
from forgeos.core.executor import Executor
from forgeos.core.observer import Observer
from forgeos.core.verifier import Verifier
from forgeos.llm.base import LLMClient
from forgeos.llm.context_manager import ContextManager
from forgeos.llm.mock import MockLLM
from forgeos.planning.planner import HierarchicalPlanner
from forgeos.planning.replan import Replanner
from forgeos.planning.scheduler import Scheduler
from forgeos.planning.task_graph import TaskGraph
from forgeos.roles.loader import RolePolicy, load_role


@dataclass
class CycleResult:
    ok: bool
    project: Path
    task_id: str
    report_path: Path | None
    evidence: list[str]
    message: str
    failure_class: str = ""


@dataclass
class StepsResult:
    ok: bool
    cycles: list[CycleResult] = field(default_factory=list)
    message: str = ""


class Orchestrator:
    def __init__(
        self,
        workspace: Path,
        project_name: str,
        role_id: str = "ceo",
        llm: LLMClient | None = None,
        context: ContextManager | None = None,
        use_context: bool = False,
        max_attempts: int = 3,
    ) -> None:
        self.workspace = workspace.resolve()
        self.project_name = project_name
        self.project = ws.project_root(self.workspace, project_name)
        self.role_id = role_id
        self.llm = llm or MockLLM()
        self.context = context or ContextManager(project_root=self.project)
        self.use_context = use_context
        self.planner = HierarchicalPlanner(self.llm)
        self.scheduler = Scheduler()
        self.replanner = Replanner(max_attempts=max_attempts)
        self.classifier = FailureClassifier()
        self.verifier = Verifier()
        self._llm_guard = False

    def _with_llm_guard(self, fn):
        if self._llm_guard:
            raise RuntimeError("orchestrator: concurrent LLM use rejected")
        self._llm_guard = True
        try:
            return fn()
        finally:
            self._llm_guard = False

    def ensure_plan(self, goal: str, *, force: bool = False) -> TaskGraph:
        graph = TaskGraph.load(ws.tasks_path(self.project))
        role = load_role(self.workspace, self.role_id)
        prompt = None
        if self.use_context:
            prompt = self.context.build(
                goal=goal,
                role_id=role.id,
                allowed_tools=list(role.allowed_tools),
                extra=(
                    "Return JSON tasks with filesystem.write actions under .forge/reports/ "
                    "when possible."
                ),
            )

        def _plan():
            return self.planner.ensure_plan(goal, graph, prompt=prompt, force=force)

        self._with_llm_guard(_plan)
        graph.save(ws.tasks_path(self.project))
        return graph

    def run_once(self, goal: str = "Phase 1 stub: write hello report") -> CycleResult:
        state = ws.load(self.project)
        graph = TaskGraph.load(ws.tasks_path(self.project))

        if not graph.tasks:
            self.ensure_plan(goal)
            graph = TaskGraph.load(ws.tasks_path(self.project))

        task = self.scheduler.next_task(graph)
        if task is None:
            counts = graph.update_counts()
            state["tasks"] = counts
            ws.save(self.project, state)
            graph.save(ws.tasks_path(self.project))
            return CycleResult(
                True,
                self.project,
                "",
                None,
                [],
                "no READY tasks",
            )

        role = load_role(self.workspace, task.role or self.role_id)
        task.status = "RUNNING"
        graph.save(ws.tasks_path(self.project))

        executor = Executor(self.project, role)
        fs = executor.fs
        self._assert_tool_allowed(role, task.action.get("tool", ""))
        exec_result = executor.execute(task.action)
        observer = Observer(fs)

        if not exec_result.ok:
            classification = self.classifier.classify(
                exec_result.detail,
                tool=exec_result.tool,
                exit_code=exec_result.exit_code,
            )
            replan = self.replanner.on_failure(
                graph,
                task,
                exec_result.detail,
                failure_class=classification.failure_class,
            )
            exec_obs = observer.observe_exec(exec_result)
            verify = self.verifier.verify(task, exec_obs)
            if verify.bundle:
                verify.bundle.failure_class = classification.failure_class
                verify.bundle.write_yaml(ws.reports_dir(self.project))
            counts = graph.update_counts()
            state["tasks"] = counts
            ws.save(self.project, state)
            graph.save(ws.tasks_path(self.project))
            evidence = [
                exec_result.detail,
                f"Failure class: {classification.failure_class} ({classification.confidence})",
                replan.message,
            ]
            report = self._write_report(
                goal,
                task.id,
                False,
                evidence,
                role,
                failure_class=classification.failure_class,
            )
            return CycleResult(
                False,
                self.project,
                task.id,
                report,
                evidence,
                replan.message,
                failure_class=classification.failure_class,
            )

        rel_path = str(task.action.get("path", ""))
        observation = observer.observe_file(rel_path)
        exec_obs = observer.observe_exec(exec_result)

        task.status = "VERIFYING"
        verify = self.verifier.verify(task, observation, exec_observation=exec_obs)
        task.evidence = list(verify.evidence)
        failure_class = ""
        if verify.ok:
            task.status = "COMPLETED"
            task.artifacts = [rel_path] if rel_path else list(task.artifacts)
            message = "cycle completed"
            evidence = list(verify.evidence)
        else:
            classification = self.classifier.classify(
                "; ".join(verify.failures),
                tool=str(task.action.get("tool", "")),
                exit_code=exec_result.exit_code,
            )
            failure_class = classification.failure_class
            replan = self.replanner.on_failure(
                graph,
                task,
                "; ".join(verify.failures),
                failure_class=failure_class,
            )
            message = replan.message
            evidence = list(verify.evidence) + list(verify.failures)
            evidence.append(f"Failure class: {failure_class} ({classification.confidence})")

        if verify.bundle:
            verify.bundle.failure_class = failure_class
            verify.bundle.write_yaml(ws.reports_dir(self.project))

        counts = graph.update_counts()
        state["tasks"] = counts
        ws.save(self.project, state)
        graph.save(ws.tasks_path(self.project))

        report = self._write_report(
            goal,
            task.id,
            verify.ok,
            evidence,
            role,
            failure_class=failure_class,
        )
        return CycleResult(
            verify.ok,
            self.project,
            task.id,
            report,
            evidence,
            message,
            failure_class=failure_class,
        )

    def run_steps(self, goal: str, steps: int = 1) -> StepsResult:
        cycles: list[CycleResult] = []
        for _ in range(max(1, steps)):
            graph = TaskGraph.load(ws.tasks_path(self.project))
            if any(t.status == "BLOCKED" for t in graph.tasks):
                return StepsResult(False, cycles, "blocked for human review")
            result = self.run_once(goal=goal)
            cycles.append(result)
            if result.task_id == "" and result.message == "no READY tasks":
                return StepsResult(True, cycles, "all scheduled work done")
            if not result.ok and "blocked" in result.message.lower():
                return StepsResult(False, cycles, result.message)
        ok = all(c.ok or c.task_id == "" for c in cycles)
        return StepsResult(ok, cycles, f"completed {len(cycles)} cycle(s)")

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
        *,
        failure_class: str = "",
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
        ]
        if failure_class:
            lines.append(f"Failure class: {failure_class}")
        lines.extend(["", "## Evidence", ""])
        lines.extend(f"- {item}" for item in evidence)
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
