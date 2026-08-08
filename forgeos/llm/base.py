"""Shared LLM client protocol and errors."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class LLMError(RuntimeError):
    """Raised when an LLM backend fails or is unreachable."""


@runtime_checkable
class LLMClient(Protocol):
    def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str: ...
