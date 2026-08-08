"""Resource governor — unload models and cap context (Phase 13)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any

from forgeos.llm.context_manager import DEFAULT_BUDGET

PRESSURE_BUDGET = 4000
VRAM_PRESSURE_RATIO = 0.85
PLAN_NUM_CTX = 2048
CODING_NUM_CTX = 4096


@dataclass
class VramSnapshot:
    used_mib: float | None = None
    total_mib: float | None = None

    @property
    def ratio(self) -> float | None:
        if self.used_mib is None or self.total_mib is None or self.total_mib <= 0:
            return None
        return self.used_mib / self.total_mib


def query_vram() -> VramSnapshot:
    """Best-effort nvidia-smi VRAM query (no bench dependency)."""
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return VramSnapshot()
    if completed.returncode != 0 or not (completed.stdout or "").strip():
        return VramSnapshot()
    line = completed.stdout.strip().splitlines()[0]
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return VramSnapshot()
    try:
        return VramSnapshot(used_mib=float(parts[0]), total_mib=float(parts[1]))
    except ValueError:
        return VramSnapshot()


class ResourceGovernor:
    """Unload Ollama models after use; shrink prompt budget under VRAM pressure."""

    def __init__(
        self,
        *,
        default_budget: int = DEFAULT_BUDGET,
        pressure_budget: int = PRESSURE_BUDGET,
        pressure_ratio: float = VRAM_PRESSURE_RATIO,
    ) -> None:
        self.default_budget = default_budget
        self.pressure_budget = pressure_budget
        self.pressure_ratio = pressure_ratio

    def prompt_budget(self, *, vram: VramSnapshot | None = None) -> int:
        snap = vram if vram is not None else query_vram()
        ratio = snap.ratio
        if ratio is not None and ratio >= self.pressure_ratio:
            return self.pressure_budget
        return self.default_budget

    def num_ctx_for(self, task_class: str) -> int:
        if task_class == "planning":
            return PLAN_NUM_CTX
        return CODING_NUM_CTX

    def unload_llm(self, llm: Any) -> bool:
        """Best-effort unload of current RoutedLLM / ModelRouter model."""
        try:
            router = getattr(llm, "router", None)
            if router is None:
                return False
            model = getattr(router, "current_model", None)
            client = getattr(router, "client", None)
            if not model or client is None or not hasattr(client, "unload"):
                return False
            client.unload(model)
            router.current_model = None
            return True
        except Exception:
            return False
