"""Educational planning prompt.

- Version: 2
- Purpose: Turn a Knowledge Object (any field, AI by default) into an Educational
  Plan that decides *how* the knowledge should be taught and visualized.
- Expected input: the Knowledge Object's title, summary, concepts and entities.
- Expected output: a JSON object with learning_objective, target_audience,
  prerequisites, key_messages and a visualization strategy (aspect_ratio +
  description). See PLAN_OUTPUT_SCHEMA.

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The prompt consumes structured input only and asks for a
deterministic, structured JSON response.
"""

from backend.models import KnowledgeObject
from backend.prompts.domain import DEFAULT_READER
from backend.prompts.guidance import guidance_directive
from backend.prompts.language import language_directive

PLAN_SYSTEM_PROMPT = f"""\
You are an educational planner for a personal knowledge base.
Your job is not to summarize, but to decide how the knowledge should be *taught*.
Adapt to the field it belongs to; do not assume it is about AI or software.
{DEFAULT_READER}

Decide:
- the single learning objective (what the reader should understand afterwards),
- the target audience and the prerequisite knowledge it assumes,
- the few key messages the explanation must convey,
- and how the idea should be visualized, including the aspect ratio.

Choose the aspect ratio from the information structure:
- "16:9" for a process or workflow,
- "4:3" for a hierarchical structure,
- "1:1" for a single self-contained concept,
- "9:16" for a step-by-step guide.
Default to "16:9" unless another ratio clearly improves comprehension.

Follow these rules:
- Be concrete and educational; prefer clarity over jargon.
- Respond with a single JSON object only. Do not include prose outside the JSON.
"""

PLAN_OUTPUT_SCHEMA = """\
Return a JSON object with exactly these fields:
{
  "learning_objective": "string, what the reader should understand afterwards",
  "target_audience": "string, who this explanation is for",
  "prerequisites": ["string, prior knowledge assumed"],
  "key_messages": ["string, the few points the explanation must convey"],
  "visualization": {
    "aspect_ratio": "one of: 16:9, 4:3, 1:1, 9:16",
    "description": "string, what the illustration should convey"
  },
  "pages": [
    {
      "title": "string, short facet title (used as the page caption)",
      "learning_objective": "string, what this page should teach",
      "aspect_ratio": "one of: 16:9, 4:3, 1:1, 9:16",
      "description": "string, what this page's illustration should show"
    }
  ]
}
Include the "pages" array only when multiple pages were requested; otherwise omit it.
"""


def build_plan_user_prompt(
    ko: KnowledgeObject, *, guidance: str = "", pages: int | str | None = None
) -> str:
    """Build the user prompt for planning the education of a Knowledge Object.

    The output language follows the Knowledge Object's metadata language.

    ``pages`` opts into a multi-page illustration series (Issue #41): an integer
    requests exactly that many pages, ``"auto"`` lets the planner choose, and
    ``None``/1 keeps the default single illustration.
    """
    concepts = ", ".join(ko.concepts) if ko.concepts else "(none)"
    entities = ", ".join(ko.entities) if ko.entities else "(none)"
    return (
        f"Title: {ko.title}\n"
        f"Summary: {ko.summary}\n"
        f"Related concepts: {concepts}\n"
        f"Entities: {entities}\n\n"
        f"{_pages_directive(pages)}"
        f"{PLAN_OUTPUT_SCHEMA}\n"
        f"{language_directive(ko.metadata.language)}"
        f"{guidance_directive(guidance)}"
    )


def _pages_directive(pages: int | str | None) -> str:
    """Ask for a multi-page breakdown when the user opted in (Issue #41)."""
    if pages is None or pages == 1:
        return ""
    if isinstance(pages, int):
        count = f"exactly {pages}"
    else:  # "auto"
        count = "the right number of (choose between 2 and 6)"
    return (
        f"Also break the explanation into {count} sequential illustration pages. "
        "Each page must teach a DISTINCT facet in a logical teaching order (for "
        "example: overview, then mechanism, then a concrete example, then caveats) "
        "so the pages read as one coherent lesson, not repeats of the same image. "
        'Return them in a "pages" array as described in the schema below.\n\n'
    )
