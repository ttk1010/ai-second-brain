"""Domain-independence guards for the extraction and planning prompts (Issue #34).

These pin the decision that prompts no longer hardcode an AI / software-engineer
audience, and that every system prompt shares the same default reader.
"""

import pytest

from backend.prompts.domain import DEFAULT_READER
from backend.prompts.extraction.comparison import COMPARISON_SYSTEM_PROMPT
from backend.prompts.extraction.concept import CONCEPT_SYSTEM_PROMPT
from backend.prompts.extraction.news import NEWS_SYSTEM_PROMPT
from backend.prompts.planning.educational import PLAN_SYSTEM_PROMPT

ALL_SYSTEM_PROMPTS = [
    CONCEPT_SYSTEM_PROMPT,
    NEWS_SYSTEM_PROMPT,
    COMPARISON_SYSTEM_PROMPT,
    PLAN_SYSTEM_PROMPT,
]


@pytest.mark.parametrize("prompt", ALL_SYSTEM_PROMPTS)
def test_prompt_does_not_hardcode_ai_or_software_audience(prompt: str) -> None:
    assert "software engineer" not in prompt
    assert "AI knowledge base" not in prompt


@pytest.mark.parametrize("prompt", ALL_SYSTEM_PROMPTS)
def test_prompt_uses_the_shared_default_reader(prompt: str) -> None:
    assert DEFAULT_READER in prompt
