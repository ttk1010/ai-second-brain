"""Monthly digest summarization prompt (Issue #39).

- Version: 1
- Purpose: Given the period's ranked AI-news headlines, write a one-line summary
  for each plus a short overall overview.
- Expected input: a numbered list of article titles (rank order).
- Expected output: a JSON object with overview, items (rank + one-line summary),
  concepts, entities (see DIGEST_OUTPUT_SCHEMA).

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). Summaries are written from the titles only (no article
fetch), so this stays cheap (ADR 0010).
"""

from backend.prompts.domain import DEFAULT_READER
from backend.prompts.guidance import guidance_directive
from backend.prompts.language import language_directive

DIGEST_SYSTEM_PROMPT = f"""\
You are an editor building a monthly digest of the most-read AI news.
You are given the period's top headlines in rank order (by access count). For
each, write a short label for an illustration AND one concise sentence explaining
what happened and why it matters; also write a short overall overview of the
month's themes. {DEFAULT_READER}

Follow these rules:
- Base each label and summary only on its title; do not invent specifics.
- "label" is for a chart tile: a self-contained phrase of about 8-16 characters
  that captures the gist (e.g. actor + action). It MUST keep at least one of the
  headline's most identifying terms — the key proper noun or subject (a product,
  model, organization, or the specific topic) — never drop them for a vague
  paraphrase. It must be COMPLETE — never cut a word mid-way, and always close any
  brackets like 「」. Drop trailing punctuation.
- "summary" is a single factual sentence (this is the accurate text; the label is
  only the short caption).
- The overview is 2-3 sentences on the month's overall themes and standouts.
- Respond with a single JSON object only. Do not include prose outside the JSON.
"""

DIGEST_OUTPUT_SCHEMA = """\
Return a JSON object with exactly these fields:
{
  "overview": "string, 2-3 sentences on the month's overall AI themes",
  "items": [
    {"rank": 1,
     "label": "string, complete 8-16 char caption for a chart tile (see rules)",
     "summary": "string, one factual sentence for the rank-1 story"}
  ],
  "concepts": ["string, recurring AI topics/technologies across the month"],
  "entities": ["string, notable organizations, models, or people this month"]
}
"""


def build_digest_user_prompt(
    titles: list[str], period: str, *, language: str = "ja", guidance: str = ""
) -> str:
    """Build the user prompt for summarizing a period's ranked headlines."""
    numbered = "\n".join(f"{i}. {title}" for i, title in enumerate(titles, start=1))
    return (
        f"Period: {period}\n"
        f"Top {len(titles)} most-read AI headlines (rank order):\n{numbered}\n\n"
        f"{DIGEST_OUTPUT_SCHEMA}\n"
        f"Provide one item per rank, in the same order.\n"
        f"{language_directive(language)}"
        f"{guidance_directive(guidance)}"
    )
