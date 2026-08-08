"""CPU / RAM / VRAM sampling helpers used by the Phase 0 benchmark.

RAM and CPU numbers come from ``psutil``. VRAM comes from shelling out to
``nvidia-smi`` (present on any machine with a working NVIDIA driver) since
there is no dependency-free cross-platform way to read GPU memory. If
``nvidia-smi`` is not available, VRAM fields are simply left as ``None`` and
the rest of the benchmark still runs.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

import psutil

_NVIDIA_SMI = shutil.which("nvidia-smi")


@dataclass(frozen=True)
class Snapshot:
    cpu_percent: float
    ram_used_mb: float
    ram_total_mb: float
    vram_used_mb: float | None
    vram_total_mb: float | None


def gpu_available() -> bool:
    return _NVIDIA_SMI is not None


def _query_vram() -> tuple[float | None, float | None]:
    if _NVIDIA_SMI is None:
        return None, None
    try:
        out = subprocess.run(
            [
                _NVIDIA_SMI,
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
        used_str, total_str = out.splitlines()[0].split(",")
        return float(used_str.strip()), float(total_str.strip())
    except (subprocess.SubprocessError, ValueError, IndexError, OSError):
        return None, None


def take_snapshot(cpu_interval: float = 0.1) -> Snapshot:
    """Sample current system resource usage.

    ``cpu_interval`` blocks briefly to get a meaningful CPU% reading (psutil
    returns 0.0 on the very first call without an interval).
    """
    cpu_percent = psutil.cpu_percent(interval=cpu_interval)
    vm = psutil.virtual_memory()
    vram_used_mb, vram_total_mb = _query_vram()
    return Snapshot(
        cpu_percent=cpu_percent,
        ram_used_mb=vm.used / (1024 * 1024),
        ram_total_mb=vm.total / (1024 * 1024),
        vram_used_mb=vram_used_mb,
        vram_total_mb=vram_total_mb,
    )


def gpu_name() -> str | None:
    if _NVIDIA_SMI is None:
        return None
    try:
        out = subprocess.run(
            [_NVIDIA_SMI, "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
        return out.splitlines()[0].strip() if out else None
    except (subprocess.SubprocessError, IndexError, OSError):
        return None


def cpu_name() -> str:
    import platform

    return platform.processor() or platform.uname().processor or "unknown"
