"""Fixed benchmark prompt set used for every model in Phase 0.

The set is intentionally small and stable across runs so results are
comparable between models. Categories map to the three reasoning modes
FORGEOS's Model Router will eventually need to pick between:

- ``simple``:   general Q&A / summarization -> general-intelligence path
- ``coding``:   generation, bug-fixing, editing -> coding path
- ``planning``: decomposing a goal into an ordered, dependency-aware
                task list -> planning / task-graph path
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkPrompt:
    id: str
    category: str
    prompt: str


PROMPTS: list[BenchmarkPrompt] = [
    # --- simple -----------------------------------------------------------
    BenchmarkPrompt(
        id="simple_explain",
        category="simple",
        prompt=(
            "Explain what a race condition is in software engineering, in three "
            "short sentences."
        ),
    ),
    BenchmarkPrompt(
        id="simple_summarize",
        category="simple",
        prompt=(
            "Summarize the following in two sentences: A task graph represents "
            "engineering work as nodes with dependencies instead of a flat "
            "to-do list, so a planner can tell that a task is blocked before "
            "wasting time on it, and can re-order remaining work when a "
            "dependency changes."
        ),
    ),
    BenchmarkPrompt(
        id="simple_qa",
        category="simple",
        prompt=(
            "What is the difference between a virtual environment and a "
            "system-wide Python install? Answer in one short paragraph."
        ),
    ),
    # --- coding -------------------------------------------------------------
    BenchmarkPrompt(
        id="coding_write_function",
        category="coding",
        prompt=(
            "Write a Python function `is_valid_email(address: str) -> bool` "
            "that does basic validation (contains exactly one '@', a non-empty "
            "local part, and a domain with at least one '.'). Only output the "
            "function code."
        ),
    ),
    BenchmarkPrompt(
        id="coding_fix_bug",
        category="coding",
        prompt=(
            "This Python function is supposed to return the average of a list "
            "of numbers but crashes on an empty list:\n\n"
            "def average(values):\n"
            "    return sum(values) / len(values)\n\n"
            "Fix it so it returns 0.0 for an empty list. Only output the "
            "corrected function."
        ),
    ),
    BenchmarkPrompt(
        id="coding_add_endpoint",
        category="coding",
        prompt=(
            "Add a `/health` GET endpoint to this FastAPI app that returns "
            '{"status": "ok"} with a 200 status code:\n\n'
            "from fastapi import FastAPI\n\napp = FastAPI()\n\n"
            "Only output the updated file."
        ),
    ),
    # --- planning -----------------------------------------------------------
    BenchmarkPrompt(
        id="planning_task_graph",
        category="planning",
        prompt=(
            "Break the feature request 'add email/password login with a "
            "password reset flow to an existing FastAPI + PostgreSQL backend' "
            "into an ordered task list. For each task, list its id, a short "
            "description, and which other task ids it depends on."
        ),
    ),
    BenchmarkPrompt(
        id="planning_next_action",
        category="planning",
        prompt=(
            "Given the current project state: 'database models exist, no API "
            "routes exist yet, no tests exist yet, git repo is clean', what is "
            "the single most useful next action to take, and why? Answer in "
            "at most 4 sentences."
        ),
    ),
    BenchmarkPrompt(
        id="planning_failure_recovery",
        category="planning",
        prompt=(
            "A task failed with error 'psycopg2.OperationalError: could not "
            "connect to server: Connection refused'. Classify the failure type, "
            "identify the most likely root cause, and propose the next task to "
            "run before retrying the original one."
        ),
    ),
]


def prompts_by_category() -> dict[str, list[BenchmarkPrompt]]:
    grouped: dict[str, list[BenchmarkPrompt]] = {}
    for p in PROMPTS:
        grouped.setdefault(p.category, []).append(p)
    return grouped
