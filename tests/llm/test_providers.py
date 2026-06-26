"""Tests for the LLM provider abstraction and OpenAI provider (Issue #7).

The OpenAI provider is tested against an injected fake client, so no real API
key or network call is required.
"""

import pytest

from backend.llm import LLMError, LLMProvider, OpenAIProvider


class _FakeMessage:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str | None) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str | None) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str | None, *, raise_exc: Exception | None = None) -> None:
        self._content = content
        self._raise = raise_exc
        self.last_kwargs: dict | None = None

    def create(self, **kwargs: object) -> _FakeResponse:
        self.last_kwargs = kwargs
        if self._raise is not None:
            raise self._raise
        return _FakeResponse(self._content)


class _FakeClient:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.chat = type("Chat", (), {"completions": completions})()


def test_openai_provider_is_an_llm_provider() -> None:
    assert isinstance(OpenAIProvider(client=_FakeClient(_FakeCompletions("x"))), LLMProvider)


def test_complete_returns_content() -> None:
    completions = _FakeCompletions("hello")
    provider = OpenAIProvider(client=_FakeClient(completions))
    assert provider.complete("sys", "user") == "hello"


def test_complete_passes_json_response_format() -> None:
    completions = _FakeCompletions("{}")
    provider = OpenAIProvider(client=_FakeClient(completions))
    provider.complete("sys", "user", response_format="json")
    assert completions.last_kwargs["response_format"] == {"type": "json_object"}


def test_complete_raises_on_empty_content() -> None:
    provider = OpenAIProvider(client=_FakeClient(_FakeCompletions(None)))
    with pytest.raises(LLMError, match="empty"):
        provider.complete("sys", "user")


def test_complete_wraps_client_errors() -> None:
    completions = _FakeCompletions("x", raise_exc=RuntimeError("boom"))
    provider = OpenAIProvider(client=_FakeClient(completions))
    with pytest.raises(LLMError, match="failed"):
        provider.complete("sys", "user")
