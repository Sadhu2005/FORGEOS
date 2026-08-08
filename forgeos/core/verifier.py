"""Verify Definition of Done with structured evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from forgeos.core.observer import Observation
from forgeos.planning.task_graph import Task


@dataclass
class EvidenceBundle:
    task_id: str
    ok: bool
    checks: dict[str, bool]
    evidence: list[str]
    failures: list[str]
    observation_notes: list[str] = field(default_factory=list)
    path: str = ""
    exit_code: int | None = None
    stdout_tail: str = ""
    failure_class: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_yaml(self, reports_dir: Path, stamp: str | None = None) -> Path:
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = reports_dir / f"evidence-{self.task_id}-{stamp}.yaml"
        path.write_text(yaml.safe_dump(self.to_dict(), sort_keys=False), encoding="utf-8")
        return path


@dataclass
class VerifyResult:
    ok: bool
    checks: dict[str, bool] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    bundle: EvidenceBundle | None = None


class Verifier:
    def verify(
        self,
        task: Task,
        observation: Observation,
        *,
        exec_observation: Observation | None = None,
    ) -> VerifyResult:
        checks: dict[str, bool] = {}
        evidence: list[str] = []
        failures: list[str] = []
        exec_obs = exec_observation

        for item in task.verification:
            key = item.strip()
            lower = key.lower()
            if lower.startswith("contains:"):
                needle = key.split(":", 1)[1]
                ok = needle in (observation.content or "")
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: contains {needle!r}")
                else:
                    failures.append(f"FAIL: missing content {needle!r}")
            elif lower.startswith("exit_code:"):
                expected = int(key.split(":", 1)[1].strip())
                code = exec_obs.exit_code if exec_obs is not None else observation.exit_code
                ok = code is not None and int(code) == expected
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: exit_code={code}")
                else:
                    failures.append(f"FAIL: exit_code want={expected} got={code}")
            elif "non-empty" in lower or "non empty" in lower:
                ok = observation.exists and observation.size > 0
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: {item} size={observation.size}")
                else:
                    failures.append(f"FAIL: {item} size={observation.size}")
            elif "exist" in lower:
                ok = observation.exists
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: {item} ({observation.path})")
                else:
                    failures.append(f"FAIL: {item} ({observation.path})")
            else:
                ok = observation.exists
                checks[item] = ok
                if ok:
                    evidence.append(f"PASS: {item}")
                else:
                    failures.append(f"FAIL: {item}")

        ok = not failures
        stdout_tail = (observation.stdout or observation.content or "")[-2000:]
        bundle = EvidenceBundle(
            task_id=task.id,
            ok=ok,
            checks=dict(checks),
            evidence=list(evidence),
            failures=list(failures),
            observation_notes=list(observation.notes),
            path=observation.path,
            exit_code=observation.exit_code,
            stdout_tail=stdout_tail,
        )
        return VerifyResult(ok=ok, checks=checks, evidence=evidence, failures=failures, bundle=bundle)
