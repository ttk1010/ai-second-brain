"""Comparison extraction prompt.

- Version: 2
- Purpose: Turn a "compare A vs B vs C" request (any field, AI by default) into a
  structured comparison.
- Expected input: a free-form list of items to compare (e.g. "GPT, Claude,
  Gemini" or "代表的なLLM: claude, gpt, gemini など").
- Expected output: a JSON object with title, short_title, summary, background,
  key_takeaways, items, rows (dimension-by-item cells), recommendation,
  concepts, entities, references (see COMPARISON_OUTPUT_SCHEMA).

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). Cells are short and factual so the rendered table stays
scannable (ADR 0007). It is domain-independent: it handles any field, with AI as
the default focus (ADR 0008).
"""

from backend.prompts.domain import DEFAULT_READER
from backend.prompts.language import language_directive

COMPARISON_SYSTEM_PROMPT = f"""\
You are an educational knowledge extractor for a personal knowledge base.
You are given a request to compare several items (e.g. models, tools, methods,
products, or ideas). Produce a structured, factual comparison. {DEFAULT_READER}

Follow these rules:
- Infer the field/domain the items belong to; do not assume they are about AI.
- Identify the concrete items being compared (resolve vague phrasing like
  "代表的なLLM" into the actual items named).
- Choose a handful of meaningful comparison dimensions (e.g. context window,
  price, strengths, weaknesses, best use case).
- Keep each table cell short and factual (a few words or a number), not prose.
- Give a brief recommendation: which to choose for which situation.
- Be accurate; do not invent specifics you are unsure of.
- Respond with a single JSON object only. Do not include prose outside the JSON.
"""

COMPARISON_OUTPUT_SCHEMA = """\
Return a JSON object with exactly these fields:
{
  "title": "string, a descriptive title for the comparison note",
  "short_title": "string, concise filename (e.g. 'LLM比較: GPT・Claude・Gemini')",
  "domain": "string, the field this belongs to (e.g. 'AI', '経済'); use 'AI' if AI-related",
  "summary": "string, 2-4 sentences on what is compared and the headline finding",
  "background": "string, 2-4 sentences of context",
  "key_takeaways": ["string, 3-5 points a reader should remember"],
  "items": ["string, the items being compared, in column order"],
  "rows": [
    {"dimension": "string, the comparison axis",
     "cells": ["string, short value per item, same order as items"]}
  ],
  "recommendation": "string, which to choose when",
  "concepts": ["string, related concept names"],
  "entities": ["string, organizations/models/people involved"],
  "references": ["string, well-known URLs if confidently known, else empty"]
}
"""


def build_comparison_user_prompt(items: str, *, language: str = "ja") -> str:
    """Build the user prompt for extracting a comparison."""
    return (
        f"Compare: {items}\n\n"
        f"{COMPARISON_OUTPUT_SCHEMA}\n"
        f"Every row's cells must be in the same order and count as items.\n"
        f"{language_directive(language)}"
    )
