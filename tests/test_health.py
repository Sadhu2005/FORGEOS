from pathlib import Path

import yaml

from forgeos.core import world_state as ws
from forgeos.intelligence.health import health_path, probe


def test_health_probe_no_tests(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "hlth")
    report = probe(root)
    assert health_path(root).is_file()
    assert report["tests"]["total"] == 0
    assert "no tests tree" in " ".join(report.get("notes") or [])
    state = ws.load(root)
    assert "tests" in state
    assert "python" in state["environment"]


def test_health_probe_with_tests(tmp_path: Path) -> None:
    root = ws.create_project(tmp_path, "hlth2")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    report = probe(root)
    data = yaml.safe_load(health_path(root).read_text(encoding="utf-8"))
    assert data["tests"]["passing"] >= 1 or data["tests"]["total"] >= 0
    assert report["environment"]["python"]
