"""OpenAI implementation of the LLM provider.

The ``openai`` SDK is imported lazily so that importing this module (and running
tests with a mock provider) never requires the package to be configured or an
API key to be present.
"""

import logging
import time
from typing import TYPE_CHECKING

from backend.llm.base import LLMError, LLMProvider, ResponseFormat
from backend.models.usage import UsageRecord, UsageRecorder

if TYPE_CHECKING:
    from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-5.4"


class OpenAIProvider(LLMProvider):
    """Text generation backed by the OpenAI API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        api_key: str | None = None,
        client: "OpenAI | None" = None,
        usage_recorder: UsageRecorder | None = None,
    ) -> None:
        self._model = model
        self._client = client
        self._api_key = api_key
        self._usage_recorder = usage_recorder

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

        started = time.perf_counter()
        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:  # OpenAI raises many error subclasses
            raise LLMError(f"OpenAI completion failed: {exc}") from exc
        self._report_usage(response, time.perf_counter() - started)

        content = response.choices[0].message.content
        if not content:
            raise LLMError("OpenAI returned an empty completion.")
        return content

    def _report_usage(self, response: object, elapsed: float) -> None:
        """Log the call's token usage and hand it to the recorder (Issue #35).

        Usage is informational: a response without it is logged and skipped,
        never treated as a failure.
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            logger.debug("OpenAI completion returned no usage data.")
            return
        details = getattr(usage, "prompt_tokens_details", None)
        record = UsageRecord(
            kind="text",
            model=self._model,
            operation="complete",
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            cached_input_tokens=getattr(details, "cached_tokens", 0) or 0,
            elapsed_seconds=elapsed,
        )
        logger.info(
            "Text usage: %s in=%d out=%d (%.1fs)",
            record.model,
            record.input_tokens,
            record.output_tokens,
            elapsed,
        )
        if self._usage_recorder is not None:
            self._usage_recorder(record)
