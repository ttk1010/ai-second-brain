"""Generate and persist illustrations into the external Obsidian Vault.

Turns a Knowledge Object into an illustration file under the Vault's image
directory and records the Vault-relative path back into ``ko.outputs`` (references
only, ADR 0001). The image bytes live in the external Vault, never in this code
repository (ADR 0002).

The aspect ratio comes from the Educational Plan when available, defaulting to
16:9 otherwise (Illustration Principles). Prompt construction is delegated to the
illustration prompt asset (PROMPT_STYLE_GUIDE.md).
"""

import logging
from pathlib import Path

from backend.image.base import ImageProvider
from backend.models import KnowledgeObject
from backend.models.educational_plan import PageSpec
from backend.models.enums import AspectRatio, ImageQuality
from backend.prompts.illustration import (
    build_illustration_page_prompt,
    build_illustration_prompt,
)
from backend.storage.paths import resolve_target, slugify_title

logger = logging.getLogger(__name__)


class IllustrationWriter:
    """Generates an illustration for a Knowledge Object and stores it in the Vault."""

    def __init__(
        self,
        vault_path: Path,
        image_provider: ImageProvider,
        *,
        image_output_dir: str = "Images",
        quality: ImageQuality = ImageQuality.MEDIUM,
        default_aspect_ratio: AspectRatio = AspectRatio.WIDE,
    ) -> None:
        self._vault_path = vault_path
        self._provider = image_provider
        self._image_output_dir = image_output_dir
        self._quality = quality
        self._default_aspect_ratio = default_aspect_ratio

    def write(
        self, ko: KnowledgeObject, *, overwrite: bool = False, guidance: str = ""
    ) -> list[Path]:
        """Generate and store the illustration(s) for ``ko``.

        Returns the absolute path(s) written (one per page) and records the
        Vault-relative reference(s): ``ko.outputs['illustration']`` always holds
        the first page, and ``ko.illustrations`` holds the ordered list when the
        Educational Plan requested a multi-page series (Issue #41). ``guidance``
        is the user's optional generation-time instruction (Issue #32).

        Raises:
            ImageError: If image generation fails (the caller decides whether to
                degrade gracefully).
        """
        folder = self._vault_path / self._image_output_dir
        folder.mkdir(parents=True, exist_ok=True)
        stem = slugify_title(ko.short_title or ko.title)

        pages = ko.educational_plan.pages if ko.educational_plan is not None else []
        if pages:
            paths = self._write_pages(
                ko, folder, stem, pages, overwrite=overwrite, guidance=guidance
            )
        else:
            paths = [self._write_single(ko, folder, stem, overwrite=overwrite, guidance=guidance)]

        relatives = [p.relative_to(self._vault_path).as_posix() for p in paths]
        ko.illustrations = relatives
        ko.outputs = {**ko.outputs, "illustration": relatives[0]}
        logger.info("Wrote %d illustration page(s): %s", len(relatives), relatives[0])
        return paths

    def _write_single(
        self, ko: KnowledgeObject, folder: Path, stem: str, *, overwrite: bool, guidance: str
    ) -> Path:
        # Regenerating a note that used to be multi-page must not leave orphans.
        _cleanup_extra_pages(folder, stem, keep=1, overwrite=overwrite)
        target = resolve_target(folder, stem, overwrite=overwrite, suffix=".png")
        self._provider.generate(
            build_illustration_prompt(ko, guidance=guidance),
            aspect_ratio=self._aspect_ratio(ko),
            quality=self._quality,
            output_path=target,
        )
        return target

    def _write_pages(
        self,
        ko: KnowledgeObject,
        folder: Path,
        stem: str,
        pages: list[PageSpec],
        *,
        overwrite: bool,
        guidance: str,
    ) -> list[Path]:
        """Generate each page in order, anchoring later pages to page 1's style.

        Page 1 is generated from the prompt alone; every later page is generated
        with page 1 supplied as a reference image, so the whole series shares one
        look while cost stays bounded to a single reference per call (Issue #41).
        """
        _cleanup_extra_pages(folder, stem, keep=len(pages), overwrite=overwrite)
        paths: list[Path] = []
        anchor: Path | None = None
        for index, page in enumerate(pages, start=1):
            page_stem = stem if index == 1 else f"{stem}-p{index}"
            target = resolve_target(folder, page_stem, overwrite=overwrite, suffix=".png")
            prompt = build_illustration_page_prompt(
                ko,
                page,
                index=index,
                total=len(pages),
                guidance=guidance,
                has_reference=anchor is not None,
            )
            self._provider.generate(
                prompt,
                aspect_ratio=page.aspect_ratio,
                quality=self._quality,
                output_path=target,
                reference_images=[anchor] if anchor is not None else None,
            )
            paths.append(target)
            if anchor is None:
                anchor = target
        return paths

    def _aspect_ratio(self, ko: KnowledgeObject) -> AspectRatio:
        if ko.educational_plan is not None:
            return ko.educational_plan.visualization_strategy.aspect_ratio
        return self._default_aspect_ratio


def _cleanup_extra_pages(folder: Path, stem: str, *, keep: int, overwrite: bool) -> None:
    """Delete stale ``{stem}-pN.png`` pages beyond ``keep`` when regenerating.

    Only runs on ``overwrite`` (regeneration in place); a fresh create has no
    prior set to clean. Prevents a shrunk series — or a series turned back into a
    single image — from leaving orphaned page files behind.
    """
    if not overwrite:
        return
    index = max(keep + 1, 2)
    while True:
        candidate = folder / f"{stem}-p{index}.png"
        if not candidate.exists():
            break
        candidate.unlink()
        logger.info("Removed stale illustration page: %s", candidate.name)
        index += 1
