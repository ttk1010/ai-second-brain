"""Educational planning prompt.

- Version: 1
- Purpose: Turn a Knowledge Object into an Educational Plan that decides *how*
  the knowledge should be taught and visualized.
- Expected input: the Knowledge Object's title, summary, concepts and entities.
- Expected output: a JSON object with learning_objective, target_audience,
  prerequisites, key_messages and a visualization strategy (aspect_ratio +
  description). See PLAN_OUTPUT_SCHEMA.

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The prompt consumes structured input only and asks for a
deterministic, structured JSON response.
"""

from backend.models import KnowledgeObject
from backend.prompts.language import language_directive

PLAN_SYSTEM_PROMPT = """\
You are an educational planner for an AI knowledge base.
Your job is not to summarize, but to decide how a concept should be *taught* to a
software engineer who knows general programming but not necessarily this topic.

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
  }
}
"""


def build_plan_user_prompt(ko: KnowledgeObject) -> str:
    """Build the user prompt for planning the education of a Knowledge Object.

    The output language follows the Knowledge Object's metadata language.
    """
    concepts = ", ".join(ko.concepts) if ko.concepts else "(none)"
    entities = ", ".join(ko.entities) if ko.entities else "(none)"
    return (
        f"Title: {ko.title}\n"
        f"Summary: {ko.summary}\n"
        f"Related concepts: {concepts}\n"
        f"Entities: {entities}\n\n"
        f"{PLAN_OUTPUT_SCHEMA}\n"
        f"{language_directive(ko.metadata.language)}"
    )
