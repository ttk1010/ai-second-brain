"""Input classification — the first branch point of the pipeline.

Decides whether raw input is an AI concept (keyword) or a URL. This is a
lightweight, deterministic, rule-based step (no LLM): the input layer should
stay extremely lightweight (PROJECT_CHARTER.md).

Per ADR 0001, Phase 1 has only two processing pipelines (Concept / News).
URLs — including research papers and documentation — are labelled NEWS for now;
non-URL text is labelled CONCEPT. Malformed URL-like input is UNKNOWN, and the
caller (extractor/service layer) decides how to handle it.
"""

from dataclasses import dataclass
from urllib.parse import urlparse

from backend.models.enums import SourceType

_URL_SCHEMES = ("http", "https")


@dataclass(frozen=True)
class Classification:
    """Result of classifying a raw input.

    Attributes:
        source_type: The classification label (ADR 0001).
        normalized_input: The trimmed input, ready for downstream extraction.
        is_url: Whether the input is a well-formed http(s) URL.
    """

    source_type: SourceType
    normalized_input: str
    is_url: bool


def classify(raw_input: str) -> Classification:
    """Classify raw user input into a Concept or News (URL) source.

    Args:
        raw_input: The user-provided keyword or URL.

    Returns:
        A Classification with the label and normalized input.

    Raises:
        ValueError: If the input is empty or whitespace only.
    """
    if raw_input is None or not raw_input.strip():
        raise ValueError("Input must not be empty.")

    normalized = raw_input.strip()

    if _looks_like_url(normalized):
        if _is_valid_url(normalized):
            # Research papers and documentation are also URLs; Phase 1 routes
            # all well-formed URLs through the News pipeline (ADR 0001).
            return Classification(SourceType.NEWS, normalized, is_url=True)
        # Looks like a URL but is malformed (e.g. "http://").
        return Classification(SourceType.UNKNOWN, normalized, is_url=False)

    return Classification(SourceType.CONCEPT, normalized, is_url=False)


def _looks_like_url(text: str) -> bool:
    return text.lower().startswith(("http://", "https://"))


def _is_valid_url(text: str) -> bool:
    try:
        parsed = urlparse(text)
    except ValueError:
        return False
    return parsed.scheme in _URL_SCHEMES and bool(parsed.netloc)
