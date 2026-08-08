from unittest.mock import MagicMock

import pytest

from forgeos.llm.base import LLMError
from forgeos.llm.ollama_client import OllamaClient


def test_complete_mocked() -> None:
    client = OllamaClient(host="http://example.invalid")
    fake = MagicMock()
    fake.generate.return_value = {"response": "hello from mock"}
    client._client = fake
    text = client.complete("Say hi", model="qwen2.5-coder:7b")
    assert text == "hello from mock"
    fake.generate.assert_called_once()
    kwargs = fake.generate.call_args.kwargs
    assert kwargs["model"] == "qwen2.5-coder:7b"
    assert kwargs["stream"] is False


def test_think_option_passed() -> None:
    client = OllamaClient()
    fake = MagicMock()
    fake.generate.return_value = {"response": "ok"}
    client._client = fake
    client.complete("x", model="qwen3:4b", options={"think": False})
    assert fake.generate.call_args.kwargs.get("think") is False


def test_unload_keep_alive_zero() -> None:
    client = OllamaClient()
    fake = MagicMock()
    fake.generate.return_value = {"response": "."}
    client._client = fake
    client.unload("qwen3:4b")
    kwargs = fake.generate.call_args.kwargs
    assert kwargs["keep_alive"] == 0
    assert kwargs["model"] == "qwen3:4b"


def test_concurrent_rejected() -> None:
    client = OllamaClient()
    client._in_flight = True
    client._lock.acquire()
    try:
        with pytest.raises(LLMError, match="concurrent"):
            client.complete("nope")
    finally:
        client._lock.release()
        client._in_flight = False


def test_num_predict_in_options() -> None:
    client = OllamaClient()
    fake = MagicMock()
    fake.generate.return_value = {"response": "ok"}
    client._client = fake
    client.complete("x", model="qwen2.5-coder:7b", options={"num_predict": 64})
    assert fake.generate.call_args.kwargs["options"]["num_predict"] == 64


def test_complete_timeout_raises() -> None:
    import time

    client = OllamaClient(timeout_s=0.05)
    fake = MagicMock()

    def slow(**_kwargs):
        time.sleep(2)
        return {"response": "late"}

    fake.generate.side_effect = slow
    client._client = fake
    with pytest.raises(LLMError, match="timed out"):
        client.complete("slow")


def test_list_models_error_wrapped() -> None:
    client = OllamaClient(host="http://127.0.0.1:1")
    fake = MagicMock()
    fake.list.side_effect = ConnectionError("down")
    client._client = fake
    with pytest.raises(LLMError, match="unreachable"):
        client.list_models()
