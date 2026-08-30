"""Prompts for revising an existing note (Issue #29)."""

from backend.prompts.revision.revise import (
    REVISE_SECTION_SYSTEM_PROMPT,
    REVISE_TARGET_SYSTEM_PROMPT,
    build_illustration_revision_prompt,
    build_section_revision_prompt,
    build_target_prompt,
)

__all__ = [
    "REVISE_SECTION_SYSTEM_PROMPT",
    "REVISE_TARGET_SYSTEM_PROMPT",
    "build_illustration_revision_prompt",
    "build_section_revision_prompt",
    "build_target_prompt",
]
