"""Concept extraction prompt.

- Version: 2
- Purpose: Turn a concept keyword (any field, AI by default) into structured
  knowledge fields.
- Expected input: a single concept name (e.g. "Transformer", "光合成").
- Expected output: a JSON object with title, summary, concepts, entities,
  references (see CONCEPT_OUTPUT_SCHEMA).

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The prompt consumes structured input only and asks for a
deterministic, structured JSON response. It is domain-independent: it handles any
field of knowledge, with AI as the default focus (ADR 0008).
"""

from backend.prompts.domain import DEFAULT_READER
from backend.prompts.guidance import guidance_directive
from backend.prompts.language import language_directive

CONCEPT_SYSTEM_PROMPT = f"""\
You are an educational knowledge extractor for a personal knowledge base.
Your job is to explain a concept clearly. {DEFAULT_READER}

Follow these rules:
- Infer the field/domain the concept belongs to and adapt the depth of
  terminology to that field; do not assume it is about AI or software.
- Be accurate and concise.
- Prefer conceptual clarity over jargon.
- Answer: what it is, why it matters, and how it works.
- Respond with a single JSON object only. Do not include prose outside the JSON.
"""

CONCEPT_OUTPUT_SCHEMA = """\
Return a JSON object with exactly these fields:
{
  "title": "string, the concept name",
  "short_title": "string, concise filename — for a concept, the concept name",
  "domain": "string, the field this belongs to (e.g. 'AI', '生物学'); use 'AI' if AI-related",
  "summary": "string, 2-4 sentence explanation",
  "background": "string, 2-4 sentences on why it matters and the context needed to understand it",
  "key_takeaways": ["string, 3-5 points a reader should remember"],
  "concepts": ["string, closely related concept names"],
  "entities": ["string, relevant organizations, models, or people"],
  "references": ["string, well-known URLs if confidently known, else empty"]
}
"""


def build_concept_user_prompt(concept: str, *, language: str = "ja", guidance: str = "") -> str:
    """Build the user prompt for extracting a concept."""
    return (
        f"Concept: {concept}\n\n"
        f"{CONCEPT_OUTPUT_SCHEMA}\n"
        f"{language_directive(language)}"
        f"{guidance_directive(guidance)}"
    )
