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


def test_complete_reports_usage_to_recorder() -> None:
    """Issue #35: each completion's token usage reaches the injected recorder."""
    completions = _FakeCompletions("hello")
    details = type("Details", (), {"cached_tokens": 40})()
    usage = type(
        "Usage",
        (),
        {"prompt_tokens": 120, "completion_tokens": 30, "prompt_tokens_details": details},
    )()
    original_create = completions.create

    def create_with_usage(**kwargs: object) -> _FakeResponse:
        response = original_create(**kwargs)
        response.usage = usage
        return response

    completions.create = create_with_usage  # type: ignore[method-assign]
    records = []
    provider = OpenAIProvider(
        model="gpt-5.4", client=_FakeClient(completions), usage_recorder=records.append
    )

    provider.complete("sys", "user")

    assert len(records) == 1
    record = records[0]
    assert (record.kind, record.model, record.operation) == ("text", "gpt-5.4", "complete")
    assert (record.input_tokens, record.output_tokens) == (120, 30)
    assert record.cached_input_tokens == 40


def test_complete_without_usage_data_still_succeeds() -> None:
    """Usage is informational: a response without it is not an error."""
    records = []
    provider = OpenAIProvider(
        client=_FakeClient(_FakeCompletions("ok")), usage_recorder=records.append
    )
    assert provider.complete("sys", "user") == "ok"
    assert records == []
