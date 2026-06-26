"""Shared language directive for prompts.

Lets prompts instruct the model which language to write the natural-language
fields in, so ``default_language`` actually controls the note's prose
(PROMPT_STYLE_GUIDE.md: prompts are model-agnostic and explicit).
"""

# Friendly names for the languages we expect; unknown codes fall back to the code
# itself, which capable models still understand.
_LANGUAGE_NAMES = {
    "ja": "Japanese",
    "en": "English",
}


def language_name(language: str) -> str:
    """Return a human-readable language name for a language code."""
    return _LANGUAGE_NAMES.get(language.lower(), language)


def language_directive(language: str) -> str:
    """Return an instruction telling the model which language to write in."""
    return (
        f"Write all natural-language text (title, summary, background, key "
        f"takeaways) in {language_name(language)}."
    )
