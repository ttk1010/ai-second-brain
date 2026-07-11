"""Educational illustration prompt.

- Version: 1
- Purpose: Turn a Knowledge Object (and its Educational Plan) into a prompt for
  generating a consistent, educational illustration.
- Expected input: a Knowledge Object whose ``educational_plan`` is preferred but
  optional (the pipeline degrades gracefully when planning failed).
- Expected output: a single prompt string suitable for an image model.

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The illustration must teach, never decorate, and always
follow the same visual language so the same concept looks consistent over time
(Illustration Principles).
"""

from backend.models import KnowledgeObject

# System layer: the long-term visual language. This rarely changes so that the
# same concept is always drawn in the same style (PROMPT_STYLE_GUIDE.md).
ILLUSTRATION_STYLE = """\
Create an educational illustration for a personal knowledge base.
The illustration must teach, not decorate: simplify complexity, reveal
relationships, explain processes, and emphasize the important concepts.

Visual style (keep consistent across every illustration):
- hand-drawn, textbook-inspired
- soft colors on a clean white background
- information-rich but visually calm
- clear labels in English; no decorative noise
Do not include photorealistic imagery, logos, or marketing aesthetics."""


def build_illustration_prompt(ko: KnowledgeObject, *, guidance: str = "") -> str:
    """Build the illustration prompt for a Knowledge Object.

    Uses the Educational Plan when present (its learning objective, key messages
    and visualization description drive the illustration). Falls back to the
    Knowledge Object's own fields when no plan is available, so an illustration
    can still be produced after a planning failure.

    ``guidance`` is the user's optional generation-time instruction (Issue #32);
    it steers the illustration so it stays consistent with the note body.
    """
    lines = [ILLUSTRATION_STYLE, "", f"Subject: {ko.title}"]

    plan = ko.educational_plan
    if plan is not None:
        lines.append(f"Teach this: {plan.learning_objective}")
        if plan.visualization_strategy.description:
            lines.append(f"Illustration focus: {plan.visualization_strategy.description}")
        if plan.key_messages:
            lines.append("Emphasize these points:")
            lines.extend(f"- {message}" for message in plan.key_messages)
        lines.append(f"Aspect ratio: {plan.visualization_strategy.aspect_ratio.value}")
    else:
        # Graceful fallback: no Educational Plan, so teach from the summary.
        lines.append(f"Teach this: {ko.summary}")
        if ko.concepts:
            lines.append("Emphasize these points:")
            lines.extend(f"- {concept}" for concept in ko.concepts)

    if guidance.strip():
        lines.append(f"Additional guidance (tone/audience/emphasis): {guidance.strip()}")

    return "\n".join(lines)
