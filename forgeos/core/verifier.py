"""Verify Definition of Done with evidence."""

from __future__ import annotations

from dataclasses import dataclass, field

from forgeos.core.observer import Observation
from forgeos.planning.task_graph import Task


@dataclass
class VerifyResult:
    ok: bool
    checks: dict[str, bool] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


class Verifier:
    def verify(self, task: Task, observation: Observation) -> VerifyResult:
        checks: dict[str, bool] = {}
        evidence: list[str] = []
        failures: list[str] = []

        for item in task.verification:
            key = item.lower()
            if "exist" in key:
                ok = observation.exists
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: {item} ({observation.path})")
                else:
                    failures.append(f"FAIL: {item} ({observation.path})")
            elif "non-empty" in key or "non empty" in key:
                ok = observation.exists and observation.size > 0
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: {item} size={observation.size}")
                else:
                    failures.append(f"FAIL: {item} size={observation.size}")
            else:
                # unknown checklist item — require existence as baseline
                ok = observation.exists
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: {item}")
                else:
                    failures.append(f"FAIL: {item}")

        return VerifyResult(ok=not failures, checks=checks, evidence=evidence, failures=failures)
