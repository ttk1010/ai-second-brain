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
from backend.models.enums import AspectRatio, ImageQuality
from backend.prompts.illustration import build_illustration_prompt
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

    def write(self, ko: KnowledgeObject, *, overwrite: bool = False) -> Path:
        """Generate and store the illustration for ``ko``.

        Returns the absolute path written and records the Vault-relative path in
        ``ko.outputs['illustration']``.

        Raises:
            ImageError: If image generation fails (the caller decides whether to
                degrade gracefully).
        """
        folder = self._vault_path / self._image_output_dir
        folder.mkdir(parents=True, exist_ok=True)

        target = resolve_target(folder, slugify_title(ko.title), overwrite=overwrite, suffix=".png")
        prompt = build_illustration_prompt(ko)

        self._provider.generate(
            prompt,
            aspect_ratio=self._aspect_ratio(ko),
            quality=self._quality,
            output_path=target,
        )

        relative = target.relative_to(self._vault_path)
        ko.outputs = {**ko.outputs, "illustration": relative.as_posix()}

        logger.info("Wrote illustration: %s", relative)
        return target

    def _aspect_ratio(self, ko: KnowledgeObject) -> AspectRatio:
        if ko.educational_plan is not None:
            return ko.educational_plan.visualization_strategy.aspect_ratio
        return self._default_aspect_ratio
