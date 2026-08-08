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
from forgeos.memory.repository import Repository
from forgeos.planning.planner import HierarchicalPlanner
from forgeos.planning.replan import Replanner
from forgeos.planning.scheduler import Scheduler
from forgeos.planning.task_graph import TaskGraph
from forgeos.roles.loader import RolePolicy, load_role
from forgeos.safety.approval import ApprovalStore
from forgeos.safety.audit import AuditLog
from forgeos.safety.permissions import check as permission_check, fingerprint
from forgeos.tools.git import GitTool


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
        self.memory = Repository(self.project)
        self.approvals = ApprovalStore(self.project)
        self.audit = AuditLog(self.project)
        self.plan_template: str | None = None
        self._llm_guard = False

    def _with_llm_guard(self, fn):
        if self._llm_guard:
            raise RuntimeError("orchestrator: concurrent LLM use rejected")
        self._llm_guard = True
        try:
            return fn()
        finally:
            self._llm_guard = False

    def _sync_memory(self) -> None:
        try:
            self.memory.sync_from_yaml()
        except FileNotFoundError:
            pass
        self._refresh_intelligence_light()

    def _refresh_intelligence_light(self) -> None:
        try:
            from forgeos.intelligence import refresh_light

            refresh_light(self.project)
        except Exception:
            return

    def _record_cycle_event(
        self,
        *,
        task_id: str,
        ok: bool,
        message: str,
        failure_class: str = "",
        kind: str = "cycle",
    ) -> None:
        self.memory.add_event(
            kind=kind,
            task_id=task_id,
            payload={
                "ok": ok,
                "message": message,
                "failure_class": failure_class,
            },
        )

    def _record_failure_decision(
        self,
        *,
        problem: str,
        chosen: str,
        confidence: str,
        reason: str,
        evidence: list[str],
        failure_class: str = "",
    ) -> None:
        self.memory.add_decision(
            problem=problem[:500],
            options=["retry", "block"],
            chosen=chosen,
            confidence=confidence,
            risk="medium" if chosen == "replan" else "high",
            reason=reason or failure_class or chosen,
            evidence=list(evidence),
        )

    def ensure_plan(
        self,
        goal: str,
        *,
        force: bool = False,
        template: str | None = None,
    ) -> TaskGraph:
        graph = TaskGraph.load(ws.tasks_path(self.project))
        role = load_role(self.workspace, self.role_id)
        plan_template = template if template is not None else self.plan_template
        from forgeos.planning.templates import is_fastapi_health_goal

        managed = (plan_template or "").startswith("fastapi") or is_fastapi_health_goal(goal)
        prompt = None
        if self.use_context:
            extra = (
                "Return a JSON array of multi-role managed-app tasks with concrete action "
                "objects (filesystem.write, testing.run with cwd=backend, docker.compose_up). "
                "Use roles software_architect, backend, devops, qa, documentation. "
                "Do not assign backend/** writes to ceo."
                if managed
                else (
                    "Return JSON tasks with filesystem.write actions under .forge/reports/ "
                    "when possible."
                )
            )
            prompt = self.context.build(
                goal=goal,
                role_id=role.id,
                allowed_tools=list(role.allowed_tools),
                extra=extra,
            )

        def _plan():
            return self.planner.ensure_plan(
                goal,
                graph,
                prompt=prompt,
                force=force,
                template=plan_template,
                project_root=self.project,
            )

        self._with_llm_guard(_plan)
        graph.save(ws.tasks_path(self.project))
        self._sync_memory()
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
            self._sync_memory()
            self._record_cycle_event(
                task_id="",
                ok=True,
                message="no READY tasks",
                kind="cycle",
            )
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

        branch = ""
        try:
            branch = GitTool(self.project).current_branch()
        except Exception:
            branch = "main"
        decision = permission_check(
            role,
            task.action,
            task_risk=str(getattr(task, "risk", "low") or "low"),
            branch=branch,
        )
        fp = fingerprint(task.id, task.action)
        if decision.kind == "deny":
            task.status = "BLOCKED"
            task.last_error = decision.reason
            counts = graph.update_counts()
            state["tasks"] = counts
            ws.save(self.project, state)
            graph.save(ws.tasks_path(self.project))
            self.audit.append(
                "permission",
                decision.reason,
                task_id=task.id,
                payload={"kind": "deny", "tool": task.action.get("tool")},
            )
            self._sync_memory()
            evidence = [decision.reason]
            report = self._write_report(goal, task.id, False, evidence, role, failure_class="permission")
            return CycleResult(
                False,
                self.project,
                task.id,
                report,
                evidence,
                f"blocked by permission: {decision.reason}",
                failure_class="permission",
            )

        if decision.kind == "need_approval":
            if not self.approvals.is_approved(fp):
                ticket = self.approvals.request(
                    project_name=self.project_name,
                    task_id=task.id,
                    action=dict(task.action),
                    risk=decision.risk or "critical",
                    reason=decision.reason,
                )
                task.status = "BLOCKED"
                task.last_error = f"awaiting approval {ticket['id']}: {decision.reason}"
                counts = graph.update_counts()
                state["tasks"] = counts
                ws.save(self.project, state)
                graph.save(ws.tasks_path(self.project))
                self.audit.append(
                    "approval",
                    f"pending {ticket['id']}",
                    task_id=task.id,
                    payload={"approval_id": ticket["id"], "reason": decision.reason},
                )
                self.memory.add_decision(
                    problem=decision.reason[:500],
                    options=["approve", "reject"],
                    chosen="await_human",
                    confidence="HIGH",
                    risk=decision.risk or "critical",
                    reason=f"approval required: {ticket['id']}",
                    evidence=[ticket["id"], decision.reason],
                )
                self._sync_memory()
                evidence = [f"approval pending: {ticket['id']}", decision.reason]
                report = self._write_report(
                    goal, task.id, False, evidence, role, failure_class="permission"
                )
                return CycleResult(
                    False,
                    self.project,
                    task.id,
                    report,
                    evidence,
                    f"blocked for human review: approval {ticket['id']}",
                    failure_class="permission",
                )
            self.audit.append(
                "approval",
                "approved ticket consumed",
                task_id=task.id,
                payload={"fingerprint": fp},
            )
        elif decision.kind == "allow" and "without human gate" in decision.reason:
            self.audit.append(
                "permission",
                decision.reason,
                task_id=task.id,
                payload={"kind": "allow_critical", "tool": task.action.get("tool")},
            )

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
            chosen = "block" if replan.blocked else "replan"
            self._sync_memory()
            self._record_cycle_event(
                task_id=task.id,
                ok=False,
                message=replan.message,
                failure_class=classification.failure_class,
                kind="classify" if classification.failure_class else "cycle",
            )
            self._record_failure_decision(
                problem=exec_result.detail,
                chosen=chosen,
                confidence=classification.confidence,
                reason=replan.message,
                evidence=evidence,
                failure_class=classification.failure_class,
            )
            if replan.fix_task is not None:
                self.memory.add_event(
                    kind="replan",
                    task_id=task.id,
                    payload={"fix_task_id": replan.fix_task.id, "message": replan.message},
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
        replan = None
        classification = None
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
        self._sync_memory()
        self._record_cycle_event(
            task_id=task.id,
            ok=verify.ok,
            message=message,
            failure_class=failure_class,
            kind="verify" if verify.bundle else "cycle",
        )
        if not verify.ok and replan is not None and classification is not None:
            chosen = "block" if replan.blocked else "replan"
            self._record_failure_decision(
                problem="; ".join(verify.failures) or message,
                chosen=chosen,
                confidence=classification.confidence,
                reason=replan.message,
                evidence=evidence,
                failure_class=failure_class,
            )
            if replan.fix_task is not None:
                self.memory.add_event(
                    kind="replan",
                    task_id=task.id,
                    payload={"fix_task_id": replan.fix_task.id, "message": replan.message},
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
