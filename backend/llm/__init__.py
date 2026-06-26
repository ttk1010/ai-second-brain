"""LLM provider abstraction and implementations.

Provider layer (parallel to the image package). Core modules depend only on the
abstract ``LLMProvider`` (ADR 0002 records this package).
"""

from backend.llm.base import LLMError, LLMProvider, ResponseFormat
from backend.llm.openai_provider import OpenAIProvider

__all__ = ["LLMError", "LLMProvider", "OpenAIProvider", "ResponseFormat"]
