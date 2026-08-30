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

from backend.models import KnowledgeObject, PageSpec

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
    if ko.digest is not None and ko.digest.items:
        return _digest_illustration_prompt(ko, guidance=guidance)

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


def build_illustration_page_prompt(
    ko: KnowledgeObject,
    page: PageSpec,
    *,
    index: int,
    total: int,
    guidance: str = "",
    has_reference: bool = False,
) -> str:
    """Build the prompt for one page of a multi-page illustration series (Issue #41).

    Each page teaches a distinct facet (``page``) of the same Knowledge Object,
    but the whole series must look like one coherent lesson. The series context
    (page k of n, same style/characters) is injected so the pages stay visually
    consistent. When ``has_reference`` is set, the first page is supplied to the
    image model as a reference image, so the prompt tells it to match that style.
    """
    lines = [
        ILLUSTRATION_STYLE,
        "",
        f"This is page {index} of {total} in ONE consistent illustration series about: {ko.title}.",
        f"This page teaches: {page.learning_objective}",
        f"Page title (draw as a short caption): {page.title}",
    ]
    if page.description:
        lines.append(f"Illustration focus: {page.description}")
    lines.append(
        "Keep the SAME visual style, color palette, line quality, and any recurring"
        " characters or objects as the other pages in the series; only the content"
        " of this page changes."
    )
    if has_reference:
        lines.append(
            "A reference image from page 1 is provided: match its style, palette,"
            " and characters exactly while showing this page's own content."
        )
    lines.append(f"Aspect ratio: {page.aspect_ratio.value}")
    if guidance.strip():
        lines.append(f"Additional guidance (tone/audience/emphasis): {guidance.strip()}")
    return "\n".join(lines)


# The digest illustration is a single-image monthly overview (Issue #39, layout C).
# Text in a generated image is unreliable, so the image carries a short, complete
# caption per item (the extractor's label); the accurate one-line summaries live
# in the note. Fallback truncation only applies when no label was produced.
_DIGEST_LABEL_MAX = 16


def _digest_illustration_prompt(ko: KnowledgeObject, *, guidance: str = "") -> str:
    digest = ko.digest
    lines = [
        ILLUSTRATION_STYLE,
        "",
        f"Subject: a single-image monthly overview of the top AI news — {ko.title}.",
        "Compose one information-rich overview image that reads at a glance:",
        "- Number every story with its rank.",
        "- Make ranks 1-3 the heroes: larger tiles, each a detailed, specific little"
        " scene for that story (relevant objects, a small diagram or symbols), not a"
        " generic icon.",
        "- Show ranks 4-10 as a tidy numbered grid of smaller tiles, each with its own"
        " clear icon and caption — draw them with real detail, not empty boxes.",
        "- Render each caption exactly as given: short but COMPLETE — never cut a word"
        " and never leave a bracket like 「 unclosed. Do not add long sentences.",
        "Items (rank — caption):",
    ]
    for item in digest.items:
        caption = item.label.strip() or item.title[:_DIGEST_LABEL_MAX].strip()
        lines.append(f"- {item.rank}. {caption}")
    lines.append("Aspect ratio: 16:9")
    if guidance.strip():
        lines.append(f"Additional guidance (tone/audience/emphasis): {guidance.strip()}")
    return "\n".join(lines)
