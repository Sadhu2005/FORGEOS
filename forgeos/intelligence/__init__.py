"""Local engineering intelligence: health, debt, research hooks."""

from forgeos.intelligence.debt import debt_path, scan as debt_scan
from forgeos.intelligence.health import health_path, probe as health_probe
from forgeos.intelligence.research import search as research_search

__all__ = [
    "debt_path",
    "debt_scan",
    "health_path",
    "health_probe",
    "refresh_light",
    "research_search",
]


def refresh_light(project) -> dict:
    """Cheap post-plan/run refresh: debt scan only (no pytest)."""
    return debt_scan(project)
