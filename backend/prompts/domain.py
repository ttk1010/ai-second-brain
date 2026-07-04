"""Shared domain-independence directives for extraction and planning prompts.

The knowledge base handles any field of knowledge, with AI as the default focus
(ADR 0008). These constants keep the default reader and domain guidance identical
across the concept, news, comparison, and planning prompts, so tone stays
consistent no matter the field.

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md).
"""

# The default audience, applied across every field. Individual prompts adapt the
# depth of terminology to the inferred domain, but write for this reader by
# default (Issue #34, decision B). Per-note overrides are a future extension (#32).
DEFAULT_READER = (
    "Write for a curious, generally-educated learner who is new to this topic; "
    "assume general knowledge but not expertise in this specific field."
)
