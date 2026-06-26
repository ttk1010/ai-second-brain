"""Concept extraction prompt.

- Version: 1
- Purpose: Turn an AI concept keyword into structured knowledge fields.
- Expected input: a single concept name (e.g. "Transformer").
- Expected output: a JSON object with title, summary, concepts, entities,
  references (see CONCEPT_OUTPUT_SCHEMA).

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The prompt consumes structured input only and asks for a
deterministic, structured JSON response.
"""

from backend.prompts.language import language_directive

CONCEPT_SYSTEM_PROMPT = """\
You are an educational knowledge extractor for an AI knowledge base.
Your job is to explain an AI concept clearly for a software engineer who is
familiar with general programming but not necessarily with this concept.

Follow these rules:
- Be technically accurate and concise.
- Prefer conceptual clarity over jargon.
- Answer: what it is, why it matters, and how it works.
- Respond with a single JSON object only. Do not include prose outside the JSON.
"""

CONCEPT_OUTPUT_SCHEMA = """\
Return a JSON object with exactly these fields:
{
  "title": "string, the concept name",
  "summary": "string, 2-4 sentence explanation",
  "background": "string, 2-4 sentences on why it matters and the context needed to understand it",
  "key_takeaways": ["string, 3-5 points a reader should remember"],
  "concepts": ["string, closely related concept names"],
  "entities": ["string, relevant organizations, models, or people"],
  "references": ["string, well-known URLs if confidently known, else empty"]
}
"""


def build_concept_user_prompt(concept: str, *, language: str = "ja") -> str:
    """Build the user prompt for extracting a concept."""
    return f"Concept: {concept}\n\n{CONCEPT_OUTPUT_SCHEMA}\n{language_directive(language)}"
