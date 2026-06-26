"""OpenAI implementation of the LLM provider.

The ``openai`` SDK is imported lazily so that importing this module (and running
tests with a mock provider) never requires the package to be configured or an
API key to be present.
"""

from typing import TYPE_CHECKING

from backend.llm.base import LLMError, LLMProvider, ResponseFormat

if TYPE_CHECKING:
    from openai import OpenAI

DEFAULT_MODEL = "gpt-5.4"


class OpenAIProvider(LLMProvider):
    """Text generation backed by the OpenAI API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        api_key: str | None = None,
        client: "OpenAI | None" = None,
    ) -> None:
        self._model = model
        self._client = client
        self._api_key = api_key

    def _get_client(self) -> "OpenAI":
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - defensive
                raise LLMError("The 'openai' package is required for OpenAIProvider.") from exc
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def complete(
        self,
        system: str,
        user: str,
        *,
        response_format: ResponseFormat = "text",
    ) -> str:
        client = self._get_client()
        kwargs: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:  # OpenAI raises many error subclasses
            raise LLMError(f"OpenAI completion failed: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("OpenAI returned an empty completion.")
        return content
