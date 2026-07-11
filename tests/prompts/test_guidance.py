"""Guidance directive and its injection into every prompt (Issue #32)."""

import pytest

from backend.models import KnowledgeObject, Source, SourceType
from backend.parser.fetcher import FetchedArticle
from backend.prompts.extraction.comparison import build_comparison_user_prompt
from backend.prompts.extraction.concept import build_concept_user_prompt
from backend.prompts.extraction.news import build_news_user_prompt
from backend.prompts.guidance import guidance_directive
from backend.prompts.illustration import build_illustration_prompt
from backend.prompts.planning.educational import build_plan_user_prompt

GUIDANCE = "高校生向けに、歴史的背景を含めて"


def test_directive_is_empty_when_blank() -> None:
    assert guidance_directive("") == ""
    assert guidance_directive("   ") == ""


def test_directive_includes_the_text_when_present() -> None:
    out = guidance_directive("  " + GUIDANCE + "  ")
    assert GUIDANCE in out
    assert "Additional guidance" in out


def _ko() -> KnowledgeObject:
    return KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="Transformer"),
        title="Transformer",
        summary="A neural network architecture.",
        concepts=["attention"],
    )


ARTICLE = FetchedArticle(url="https://example.com/x", title="T", text="body")

BUILDERS = [
    lambda g: build_concept_user_prompt("Transformer", guidance=g),
    lambda g: build_news_user_prompt(ARTICLE, guidance=g),
    lambda g: build_comparison_user_prompt("GPT, Claude", guidance=g),
    lambda g: build_plan_user_prompt(_ko(), guidance=g),
    lambda g: build_illustration_prompt(_ko(), guidance=g),
]


@pytest.mark.parametrize("build", BUILDERS)
def test_guidance_reaches_every_prompt(build) -> None:
    assert GUIDANCE in build(GUIDANCE)


@pytest.mark.parametrize("build", BUILDERS)
def test_prompts_unchanged_without_guidance(build) -> None:
    assert "Additional guidance" not in build("")
