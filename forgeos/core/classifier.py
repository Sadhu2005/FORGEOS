"""Rule-based failure classifier (Phase 5)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

FailureClass = Literal[
    "syntax",
    "dependency",
    "logic",
    "env",
    "permission",
    "timeout",
    "unknown",
]

# Order matters: first match wins.
_RULES: list[tuple[FailureClass, re.Pattern[str], str, str]] = [
    (
        "permission",
        re.compile(
            r"PathNotAllowedError|tool not allowed|TerminalDeniedError|GitDangerousError|"
            r"not allowed by role|command denied by policy|force-push is refused|reset --hard is refused",
            re.I,
        ),
        "HIGH",
        "permission or policy denial",
    ),
    (
        "timeout",
        re.compile(r"timeout after|TimeoutExpired|timed out", re.I),
        "HIGH",
        "operation timed out",
    ),
    (
        "syntax",
        re.compile(
            r"SyntaxError|IndentationError|parse error|unexpected token|invalid syntax",
            re.I,
        ),
        "HIGH",
        "syntax/parse error",
    ),
    (
        "dependency",
        re.compile(
            r"ModuleNotFoundError|ImportError|No module named|not found on PATH|"
            r"missing package|pip install|Cannot find module",
            re.I,
        ),
        "HIGH",
        "missing dependency",
    ),
    (
        "logic",
        re.compile(
            r"AssertionError|FAIL:|content mismatch|missing content|wrong result|"
            r"non-empty|assert ",
            re.I,
        ),
        "MEDIUM",
        "logic or verification failure",
    ),
    (
        "env",
        re.compile(
            r"connection refused|unreachable|docker binary not found|Permission denied|"
            r"No such file|FileNotFoundError|compose file missing|ollama unreachable",
            re.I,
        ),
        "MEDIUM",
        "environment or runtime issue",
    ),
]


@dataclass
class Classification:
    failure_class: FailureClass
    confidence: str
    reason: str


class FailureClassifier:
    def classify(
        self,
        message: str,
        *,
        tool: str | None = None,
        exit_code: int | None = None,
    ) -> Classification:
        text = message or ""
        if tool:
            text = f"{text} tool={tool}"
        if exit_code is not None:
            text = f"{text} exit_code={exit_code}"

        for failure_class, pattern, confidence, reason in _RULES:
            if pattern.search(text):
                return Classification(failure_class, confidence, reason)

        if exit_code not in (None, 0):
            return Classification("logic", "LOW", f"non-zero exit_code={exit_code}")

        return Classification("unknown", "LOW", "no matching failure rule")
