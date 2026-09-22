"""Tests for the illustration prompt builder (Issue #12)."""

from backend.models import (
    AspectRatio,
    EducationalPlan,
    IllustrationStyle,
    KnowledgeObject,
    PageSpec,
    Source,
    SourceType,
    VisualizationStrategy,
)
from backend.prompts.illustration import (
    ILLUSTRATION_STYLE,
    ILLUSTRATION_STYLE_EXPLICIT,
    build_illustration_page_prompt,
    build_illustration_prompt,
)


def _ko(*, plan: EducationalPlan | None) -> KnowledgeObject:
    return KnowledgeObject(
        source=Source(type=SourceType.CONCEPT, value="Transformer"),
        title="Transformer",
        summary="A neural network architecture based on self-attention.",
        concepts=["attention", "self-attention"],
        educational_plan=plan,
    )


def _plan() -> EducationalPlan:
    return EducationalPlan(
        learning_objective="Understand how self-attention powers Transformers.",
        target_audience="Software engineers.",
        prerequisites=["neural networks"],
        key_messages=["Attention weighs tokens", "Parallelizable"],
        visualization_strategy=VisualizationStrategy(
            aspect_ratio=AspectRatio.STANDARD,
            description="A diagram of the attention mechanism.",
        ),
    )


def test_prompt_uses_plan_when_present() -> None:
    prompt = build_illustration_prompt(_ko(plan=_plan()))

    assert ILLUSTRATION_STYLE in prompt
    assert "Subject: Transformer" in prompt
    assert "Understand how self-attention powers Transformers." in prompt
    assert "A diagram of the attention mechanism." in prompt
    assert "- Attention weighs tokens" in prompt
    assert "Aspect ratio: 4:3" in prompt


def test_prompt_is_deterministic() -> None:
    ko = _ko(plan=_plan())
    assert build_illustration_prompt(ko) == build_illustration_prompt(ko)


def test_prompt_always_includes_visual_style() -> None:
    # The consistent visual language must appear even without a plan.
    prompt = build_illustration_prompt(_ko(plan=None))
    assert ILLUSTRATION_STYLE in prompt
    assert "hand-drawn" in prompt


def test_prompt_falls_back_to_summary_without_plan() -> None:
    prompt = build_illustration_prompt(_ko(plan=None))

    assert "Subject: Transformer" in prompt
    assert "A neural network architecture based on self-attention." in prompt
    assert "- attention" in prompt
    # No aspect ratio line without a plan.
    assert "Aspect ratio:" not in prompt


def test_standard_style_is_the_default() -> None:
    """Local generation keeps the original wording unless a style is chosen."""
    prompt = build_illustration_prompt(_ko(plan=_plan()))
    assert ILLUSTRATION_STYLE in prompt
    assert ILLUSTRATION_STYLE_EXPLICIT not in prompt


def test_explicit_style_spells_out_the_hand_drawn_look() -> None:
    """Issue #45: the explicit wording steers models away from flat vector art."""
    prompt = build_illustration_prompt(
        _ko(plan=_plan()), style=IllustrationStyle.EXPLICIT_HAND_DRAWN
    )
    assert ILLUSTRATION_STYLE_EXPLICIT in prompt
    assert "Avoid flat vector graphics" in prompt


def test_explicit_style_applies_to_series_pages() -> None:
    page = PageSpec(title="p", learning_objective="obj", aspect_ratio=AspectRatio.WIDE)
    prompt = build_illustration_page_prompt(
        _ko(plan=_plan()), page, index=2, total=3, style=IllustrationStyle.EXPLICIT_HAND_DRAWN
    )
    assert ILLUSTRATION_STYLE_EXPLICIT in prompt
