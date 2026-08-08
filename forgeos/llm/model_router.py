"""Model router — task class → local Ollama model (Phase 0 lock)."""

from __future__ import annotations

from typing import Any, Literal

from forgeos.llm.ollama_client import OllamaClient

TaskClass = Literal["coding", "simple", "planning"]

DEFAULT_ROUTING: dict[TaskClass, str] = {
    "coding": "qwen2.5-coder:7b",
    "simple": "qwen2.5-coder:7b",
    "planning": "qwen3:4b",
}


class ModelRouter:
    """Selects models per MODEL_ROUTING.md; unloads previous on switch."""

    def __init__(
        self,
        client: OllamaClient,
        routing: dict[str, str] | None = None,
    ) -> None:
        self.client = client
        self.routing: dict[str, str] = dict(routing or DEFAULT_ROUTING)
        self.current_model: str | None = None

    def select(self, task_class: TaskClass | str) -> str:
        key = str(task_class)
        if key not in self.routing:
            raise ValueError(f"unknown task class: {task_class}")
        return self.routing[key]

    def options_for(self, task_class: TaskClass | str) -> dict[str, Any]:
        """Planning / qwen3: prefer think disabled for latency."""
        model = self.select(task_class)
        opts: dict[str, Any] = {}
        if task_class == "planning" or model.startswith("qwen3"):
            opts["think"] = False
        return opts

    def ensure_model(self, model: str) -> str:
        if self.current_model and self.current_model != model:
            self.client.unload(self.current_model)
        self.current_model = model
        return model

    def complete(
        self,
        prompt: str,
        *,
        task_class: TaskClass | str = "simple",
    ) -> str:
        model = self.select(task_class)
        self.ensure_model(model)
        return self.client.complete(prompt, model=model, options=self.options_for(task_class))


class RoutedLLM:
    """LLMClient adapter that routes completions through ModelRouter."""

    def __init__(self, router: ModelRouter, task_class: TaskClass | str = "planning") -> None:
        self.router = router
        self.task_class = task_class
        self.call_count = 0

    def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        self.call_count += 1
        if model is not None:
            self.router.ensure_model(model)
            opts = options if options is not None else self.router.options_for(self.task_class)
            return self.router.client.complete(prompt, model=model, options=opts)
        return self.router.complete(prompt, task_class=self.task_class)
