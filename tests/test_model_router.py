from unittest.mock import MagicMock, patch

from forgeos.llm.model_router import PLAN_NUM_PREDICT, ModelRouter, RoutedLLM
from forgeos.llm.ollama_client import OllamaClient


def test_select_defaults() -> None:
    client = OllamaClient()
    router = ModelRouter(client)
    assert router.select("coding") == "qwen2.5-coder:7b"
    assert router.select("simple") == "qwen2.5-coder:7b"
    assert router.select("planning") == "qwen2.5-coder:7b"


def test_planning_options_cap() -> None:
    router = ModelRouter(OllamaClient())
    opts = router.options_for("planning")
    assert opts.get("think") is False
    assert opts.get("num_predict") == PLAN_NUM_PREDICT


def test_switch_unloads_previous() -> None:
    client = OllamaClient()
    client.unload = MagicMock()
    client.complete = MagicMock(return_value="ok")
    router = ModelRouter(
        client,
        routing={"coding": "qwen2.5-coder:7b", "simple": "a", "planning": "qwen3:4b"},
    )
    router.current_model = "qwen2.5-coder:7b"
    router.complete("plan me", task_class="planning")
    client.unload.assert_called_once_with("qwen2.5-coder:7b")
    assert router.current_model == "qwen3:4b"


def test_routed_llm_complete() -> None:
    client = OllamaClient()
    fake = MagicMock()
    fake.generate.return_value = {"response": "routed"}
    client._client = fake
    llm = RoutedLLM(ModelRouter(client), task_class="simple")
    assert llm.complete("hi") == "routed"
    assert llm.call_count == 1
