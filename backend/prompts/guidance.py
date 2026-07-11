"""Optional user guidance, shared across extraction, planning, and illustration.

Issue #32: at generation time the user can pass a free-text instruction (e.g.
"高校生向けに、歴史的背景を含めて") that steers tone, audience, and emphasis. The
same guidance is injected into every prompt so the note body and the illustration
stay consistent.

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md).
"""


def guidance_directive(guidance: str) -> str:
    """Render the user's guidance as a prompt fragment, or "" when there is none.

    The guidance steers the output but never overrides the prompt's own rules, so
    a note stays well-formed regardless of what the user asks for.
    """
    cleaned = guidance.strip()
    if not cleaned:
        return ""
    return (
        "\nAdditional guidance from the user — follow it for tone, audience, and "
        f"emphasis, as long as it does not conflict with the rules above:\n{cleaned}\n"
    )
