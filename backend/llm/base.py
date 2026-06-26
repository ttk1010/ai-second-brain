"""LLM provider abstraction.

Core modules depend on this interface, never on a concrete provider, so that
no implementation is tied to a single AI vendor (PROJECT_CHARTER.md). Concrete
providers (e.g. OpenAI) are injected via dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Literal

ResponseFormat = Literal["text", "json"]


class LLMError(Exception):
    """Raised when an LLM call fails or returns an unusable response."""


class LLMProvider(ABC):
    """Abstract text-generation provider.

    Phase 1 needs only synchronous, single-shot completion. Streaming and async
    are intentionally omitted until a concrete need arises (YAGNI).
    """

    @abstractmethod
    def complete(
        self,
        system: str,
        user: str,
        *,
        response_format: ResponseFormat = "text",
    ) -> str:
        """Return the model's completion for the given system and user prompts.

        Args:
            system: The system prompt (long-term behavior).
            user: The user/data prompt.
            response_format: Request plain text or a JSON object.

        Raises:
            LLMError: If the call fails or yields no usable content.
        """
