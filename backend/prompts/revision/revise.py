"""Revision prompts: pick a target, rewrite a section, or restyle the illustration.

- Version: 1
- Purpose: Support ``asb-revise`` (Issue #29) — improve one part of an existing
  note from a natural-language instruction, without regenerating the whole note.
- Expected input: the note's title, the current section text (for a rewrite),
  and the user's instruction.
- Expected output: a target name (JSON), the revised section text (plain text),
  or an illustration prompt string.

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The section rewrite returns ONLY the new body so the
deterministic writer can drop it into the section verbatim.
"""

from backend.prompts.illustration.educational import ILLUSTRATION_STYLE
from backend.prompts.language import language_directive

# The targets a revision can address: three editable body sections, or the
# illustration. Kept in sync with markdown.sections.EDITABLE_SECTIONS.
_TARGETS = ("summary", "background", "key_takeaways", "illustration")

REVISE_TARGET_SYSTEM_PROMPT = f"""\
You decide which single part of an existing note a revision instruction refers to.
Choose exactly one of: {", ".join(_TARGETS)}.
- "summary": the short overview of the topic.
- "background": the context and why the topic matters.
- "key_takeaways": the bulleted points to remember.
- "illustration": the educational image (redraw / restyle / change the visual).
Respond with a single JSON object: {{"target": "<one of the above>"}}.
Do not include any prose outside the JSON."""

REVISE_SECTION_SYSTEM_PROMPT = """\
You revise one section of a personal knowledge note from a natural-language
instruction. Rewrite ONLY that section's content to satisfy the instruction while
staying faithful to the topic. Keep it educational and clear.

Rules:
- Return ONLY the new section body — no heading, no code fences, no commentary.
- Preserve the section's existing format: prose stays prose; a bulleted list
  (e.g. Key Takeaways) stays a Markdown bullet list ("- ").
- Keep the same language as the current text unless the instruction says otherwise."""


def build_target_prompt(title: str, instruction: str) -> str:
    """Build the user prompt that classifies which part to revise."""
    return f"Note title: {title}\nInstruction: {instruction}\n\nWhich part does this refer to?"


def build_section_revision_prompt(
    *, title: str, section_name: str, current_text: str, instruction: str, language: str
) -> str:
    """Build the user prompt to rewrite one section's body."""
    return (
        f"Note title: {title}\n"
        f"Section: {section_name}\n"
        f"Instruction: {instruction}\n\n"
        f"Current {section_name} content:\n{current_text}\n\n"
        f"Rewrite the {section_name} content to satisfy the instruction."
        f"{language_directive(language)}"
    )


def build_illustration_revision_prompt(*, title: str, context: str, instruction: str) -> str:
    """Build the image prompt to restyle/redraw the note's illustration.

    The existing illustration is supplied to the image model as a reference image
    (``images.edit``), so this prompt asks it to apply the instruction while
    keeping the educational visual language (Issue #29 / ADR 0012).
    """
    lines = [
        ILLUSTRATION_STYLE,
        "",
        f"Subject: {title}",
        "You are given the note's current illustration as a reference image.",
        f"Revise it according to this instruction: {instruction}",
        "Keep it educational and consistent with the visual style above; change"
        " only what the instruction asks for.",
    ]
    if context.strip():
        lines.append(f"Context (what the note teaches): {context.strip()}")
    return "\n".join(lines)
