"""Shared test fixtures and helpers."""

from backend.llm.base import LLMProvider, ResponseFormat


class MockLLMProvider(LLMProvider):
    """An LLM provider that returns a canned response, for tests."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, str, ResponseFormat]] = []

    def complete(
        self,
        system: str,
        user: str,
        *,
        response_format: ResponseFormat = "text",
    ) -> str:
        self.calls.append((system, user, response_format))
        return self.response
