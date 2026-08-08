"""Deterministic MockLLM for Phase 1 (no Ollama)."""

from __future__ import annotations

import threading


class MockLLM:
    """Ensures at most one completion call is in flight at a time."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._in_flight = False
        self.call_count = 0
        self.last_prompt: str | None = None

    def complete(self, prompt: str) -> str:
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("MockLLM: concurrent call rejected (one LLM at a time)")
        try:
            if self._in_flight:
                raise RuntimeError("MockLLM: already in flight")
            self._in_flight = True
            self.call_count += 1
            self.last_prompt = prompt
            return f"MOCK_OK:{prompt[:80]}"
        finally:
            self._in_flight = False
            self._lock.release()
