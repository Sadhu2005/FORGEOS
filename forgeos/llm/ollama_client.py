"""Ollama HTTP client with one-at-a-time concurrency guard."""

from __future__ import annotations

import os
import threading
from typing import Any

from forgeos.llm.base import LLMError

DEFAULT_HOST = "http://127.0.0.1:11434"


def default_host() -> str:
    return os.environ.get("FORGEOS_OLLAMA_HOST", DEFAULT_HOST)


class OllamaClient:
    """Thin wrapper around ollama.Client with FORGEOS concurrency rules."""

    def __init__(self, host: str | None = None, default_model: str | None = None) -> None:
        self.host = host or default_host()
        self.default_model = default_model or "qwen2.5-coder:7b"
        self._lock = threading.Lock()
        self._in_flight = False
        self.call_count = 0
        self.last_prompt: str | None = None
        self.last_model: str | None = None
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import ollama
            except ImportError as exc:
                raise LLMError("ollama package not installed; pip install ollama") from exc
            self._client = ollama.Client(host=self.host)
        return self._client

    def ping(self) -> bool:
        try:
            self.list_models()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            client = self._get_client()
            response = client.list()
        except Exception as exc:  # noqa: BLE001 — surface as LLMError
            raise LLMError(f"ollama unreachable at {self.host}: {exc}") from exc
        models = getattr(response, "models", None)
        if models is None and isinstance(response, dict):
            models = response.get("models", [])
        names: list[str] = []
        for item in models or []:
            name = getattr(item, "model", None) or getattr(item, "name", None)
            if name is None and isinstance(item, dict):
                name = item.get("model") or item.get("name")
            if name:
                names.append(str(name))
        return names

    def unload(self, model: str) -> None:
        """Ask Ollama to drop a model from memory (keep_alive=0)."""
        try:
            client = self._get_client()
            client.generate(model=model, prompt=".", stream=False, keep_alive=0)
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"failed to unload model {model}: {exc}") from exc

    def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        chosen = model or self.default_model
        if not self._lock.acquire(blocking=False):
            raise LLMError("OllamaClient: concurrent call rejected (one LLM at a time)")
        try:
            if self._in_flight:
                raise LLMError("OllamaClient: already in flight")
            self._in_flight = True
            self.call_count += 1
            self.last_prompt = prompt
            self.last_model = chosen
            kwargs: dict[str, Any] = {
                "model": chosen,
                "prompt": prompt,
                "stream": False,
            }
            if options:
                # Ollama generate accepts think / options kwargs depending on version
                if "think" in options:
                    kwargs["think"] = options["think"]
                extra = {k: v for k, v in options.items() if k != "think"}
                if extra:
                    kwargs["options"] = extra
            try:
                client = self._get_client()
                response = client.generate(**kwargs)
            except LLMError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise LLMError(f"ollama generate failed ({chosen}): {exc}") from exc
            text = getattr(response, "response", None)
            if text is None and isinstance(response, dict):
                text = response.get("response", "")
            return str(text or "")
        finally:
            self._in_flight = False
            self._lock.release()
