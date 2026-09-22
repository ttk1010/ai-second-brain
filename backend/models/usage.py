"""Token usage of a single provider call (Issues #35, #45).

Providers report what each API call consumed through an optional
``UsageRecorder`` callback (dependency injection). Normal runs pass none and
only log the usage; the measurement script collects the records to compute
per-note cost and compare image models.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

UsageKind = Literal["text", "image"]


@dataclass(frozen=True)
class UsageRecord:
    """What one provider call consumed.

    ``input_tokens`` is the total input; ``cached_input_tokens`` and
    ``input_image_tokens`` are subsets of it, billed at their own rates.
    """

    kind: UsageKind
    model: str
    operation: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0
    input_image_tokens: int = 0
    elapsed_seconds: float = 0.0


UsageRecorder = Callable[[UsageRecord], None]
