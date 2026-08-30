"""Revise an existing note from a natural-language instruction (Issue #29).

Improves one part of a note without regenerating the whole thing: a body section
(Summary / Background / Key Takeaways) is rewritten in place, or the illustration
is redrawn from the instruction using the existing image as a style reference
(``images.edit``, ADR 0012). The Knowledge Object is not persisted (ADR 0005);
the current text is read back from the note's Markdown. Writes happen in place
(the Vault is Git-managed, so history lives there).
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.image.base import ImageError, ImageProvider
from backend.llm.base import LLMError, LLMProvider
from backend.markdown import (
    EDITABLE_SECTIONS,
    extract_section,
    first_embedded_image,
    replace_section,
)
from backend.models.enums import AspectRatio, ImageQuality
from backend.prompts.revision import (
    REVISE_SECTION_SYSTEM_PROMPT,
    REVISE_TARGET_SYSTEM_PROMPT,
    build_illustration_revision_prompt,
    build_section_revision_prompt,
    build_target_prompt,
)
from backend.storage import VaultWriter
from backend.storage.frontmatter import parse_frontmatter

logger = logging.getLogger(__name__)

ReviseStatus = Literal["revised", "not_found", "unsupported"]

# Context length fed to the illustration revision (keeps the image prompt tight).
_CONTEXT_CHARS = 500


@dataclass(frozen=True)
class ReviseResult:
    """Outcome of revising one note."""

    status: ReviseStatus
    message: str
    path: Path | None = None
    target: str | None = None


class NoteReviser:
    """Applies a natural-language revision to one existing note."""

    def __init__(
        self,
        vault_writer: VaultWriter,
        llm_provider: LLMProvider,
        vault_path: Path,
        *,
        image_provider: ImageProvider | None = None,
        quality: ImageQuality = ImageQuality.MEDIUM,
        default_aspect_ratio: AspectRatio = AspectRatio.WIDE,
        language: str = "ja",
    ) -> None:
        self._vault = vault_writer
        self._llm = llm_provider
        self._vault_path = vault_path
        self._image = image_provider
        self._quality = quality
        self._default_aspect_ratio = default_aspect_ratio
        self._language = language

    def revise(
        self,
        reference: str,
        instruction: str,
        *,
        section: str | None = None,
        illustration: bool = False,
    ) -> ReviseResult:
        """Revise the note named by ``reference`` per ``instruction``.

        ``section`` / ``illustration`` force the target; otherwise the target is
        classified from the instruction. Returns a result describing what changed.

        Raises:
            ValueError: If ``instruction`` is empty.
        """
        if not instruction or not instruction.strip():
            raise ValueError("A revision instruction is required.")

        note = self._vault.find_note(reference)
        if note is None:
            return ReviseResult(
                status="not_found",
                message=f"No note found for {reference!r}. Use its title or filename.",
            )

        markdown = note.read_text(encoding="utf-8")
        target = self._resolve_target(markdown, instruction, section, illustration)
        if target is None:
            return ReviseResult(
                status="unsupported",
                message=(
                    f"Unknown revision target. Choose one of: "
                    f"{', '.join(EDITABLE_SECTIONS)}, illustration."
                ),
                path=note,
            )

        if target == "illustration":
            return self._revise_illustration(note, markdown, instruction)
        return self._revise_section(note, markdown, target, instruction)

    def _resolve_target(
        self, markdown: str, instruction: str, section: str | None, illustration: bool
    ) -> str | None:
        """Return the canonical target: an editable section key, 'illustration', or None."""
        if illustration:
            return "illustration"
        if section is not None:
            key = section.strip().lower().replace(" ", "_")
            return key if key in EDITABLE_SECTIONS else None
        return self._classify_target(markdown, instruction)

    def _classify_target(self, markdown: str, instruction: str) -> str | None:
        title = self._title(markdown)
        try:
            raw = self._llm.complete(
                REVISE_TARGET_SYSTEM_PROMPT,
                build_target_prompt(title, instruction),
                response_format="json",
            )
            data = json.loads(raw)
            target = str(data.get("target") or "").strip().lower()
        except (LLMError, json.JSONDecodeError, AttributeError):
            logger.warning("Could not classify revision target for %r.", title)
            return None
        if target == "illustration" or target in EDITABLE_SECTIONS:
            return target
        return None

    def _revise_section(
        self, note: Path, markdown: str, target: str, instruction: str
    ) -> ReviseResult:
        display = EDITABLE_SECTIONS[target]
        current = extract_section(markdown, display)
        if current is None:
            return ReviseResult(
                status="unsupported",
                message=f"The note has no {display} section to revise.",
                path=note,
                target=target,
            )
        try:
            new_text = self._llm.complete(
                REVISE_SECTION_SYSTEM_PROMPT,
                build_section_revision_prompt(
                    title=self._title(markdown),
                    section_name=display,
                    current_text=current,
                    instruction=instruction,
                    language=self._language_of(markdown),
                ),
            )
        except LLMError as exc:
            return ReviseResult(
                status="unsupported",
                message=f"Revision failed: {exc}",
                path=note,
                target=target,
            )
        updated = replace_section(markdown, display, new_text.strip())
        note.write_text(updated, encoding="utf-8")
        logger.info("Revised %s in %s", display, note.name)
        return ReviseResult(
            status="revised",
            message=f"Revised {display}: {note.name}",
            path=note,
            target=target,
        )

    def _revise_illustration(self, note: Path, markdown: str, instruction: str) -> ReviseResult:
        if self._image is None:
            return ReviseResult(
                status="unsupported",
                message="Illustration revision needs image generation (do not pass --no-image).",
                path=note,
                target="illustration",
            )
        embed = first_embedded_image(markdown)
        if embed is None:
            return ReviseResult(
                status="unsupported",
                message="The note has no illustration to revise.",
                path=note,
                target="illustration",
            )
        image_path = self._vault_path / embed
        if not image_path.exists():
            return ReviseResult(
                status="unsupported",
                message=f"Illustration file not found: {embed}.",
                path=note,
                target="illustration",
            )
        prompt = build_illustration_revision_prompt(
            title=self._title(markdown),
            context=(extract_section(markdown, "Summary") or "")[:_CONTEXT_CHARS],
            instruction=instruction,
        )
        try:
            self._image.generate(
                prompt,
                aspect_ratio=self._default_aspect_ratio,
                quality=self._quality,
                output_path=image_path,
                reference_images=[image_path],
            )
        except ImageError as exc:
            return ReviseResult(
                status="unsupported",
                message=f"Illustration revision failed: {exc}",
                path=note,
                target="illustration",
            )
        logger.info("Revised illustration %s for %s", embed, note.name)
        return ReviseResult(
            status="revised",
            message=f"Revised illustration: {embed}",
            path=note,
            target="illustration",
        )

    def _title(self, markdown: str) -> str:
        return str(parse_frontmatter(markdown).get("title") or "").strip() or "the note"

    def _language_of(self, markdown: str) -> str:
        return str(parse_frontmatter(markdown).get("language") or "").strip() or self._language
