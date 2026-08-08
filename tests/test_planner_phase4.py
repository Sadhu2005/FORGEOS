from forgeos.llm.mock import MockLLM
from forgeos.planning.planner import HierarchicalPlanner, default_template, tasks_from_llm_json
from forgeos.planning.task_graph import TaskGraph


def test_default_template_chain() -> None:
    tasks = default_template("hello")
    assert len(tasks) == 2
    assert tasks[0].status == "READY"
    assert tasks[1].status == "PROPOSED"
    assert tasks[1].dependencies == ["task-001"]


def test_planner_uses_template_for_mock() -> None:
    graph = TaskGraph()
    planner = HierarchicalPlanner(MockLLM())
    planner.ensure_plan("write hello", graph)
    assert len(graph.tasks) == 2
    assert graph.get("task-001") is not None
    assert planner.llm.call_count == 1
    # second ensure does not call LLM again
    planner.ensure_plan("write hello", graph)
    assert planner.llm.call_count == 1


def test_json_parse_tasks() -> None:
    raw = [
        {
            "id": "t1",
            "description": "one",
            "status": "READY",
            "role": "ceo",
            "priority": 1,
            "action": {"tool": "filesystem.write", "path": ".forge/reports/a.md", "content": "x"},
            "verification": ["file exists"],
        }
    ]
    tasks = tasks_from_llm_json(raw, "g")
    assert tasks is not None
    assert tasks[0].id == "t1"
