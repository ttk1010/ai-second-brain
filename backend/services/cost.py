"""Estimate the USD cost of provider calls from their token usage (Issue #35).

Prices are a dated snapshot of OpenAI's published per-token rates; they change,
so the snapshot date travels with every estimate. Update ``PRICES_AS_OF`` and
``PRICES`` together, from https://developers.openai.com/api/docs/models.
"""

from dataclasses import dataclass

from backend.models.usage import UsageRecord

PRICES_AS_OF = "2026-09-22"


@dataclass(frozen=True)
class TokenPrices:
    """USD per 1M tokens.

    For text models ``input`` covers all non-cached input. Image models bill
    image input separately (``image_input``); text models have no such tokens.
    """

    input: float
    cached_input: float
    output: float
    image_input: float = 0.0


_GPT_IMAGE = TokenPrices(input=5.0, cached_input=1.25, output=30.0, image_input=8.0)

PRICES: dict[str, TokenPrices] = {
    "gpt-5.4": TokenPrices(input=2.5, cached_input=0.25, output=15.0),
    # GPT Image 2.5 keeps GPT Image 2's token rates (model page, 2026-09).
    "gpt-image-2": _GPT_IMAGE,
    "gpt-image-2.5-flare": _GPT_IMAGE,
}


class UnknownPriceError(KeyError):
    """Raised when no price snapshot exists for a model."""


def estimate_cost(record: UsageRecord, prices: dict[str, TokenPrices] = PRICES) -> float:
    """Return the estimated USD cost of one provider call.

    Raises:
        UnknownPriceError: If ``record.model`` has no price snapshot.
    """
    price = prices.get(record.model)
    if price is None:
        raise UnknownPriceError(f"No price snapshot for model {record.model!r}.")

    image_in = record.input_image_tokens
    cached = record.cached_input_tokens
    plain_in = max(record.input_tokens - image_in - cached, 0)

    total = (
        plain_in * price.input
        + cached * price.cached_input
        + image_in * price.image_input
        + record.output_tokens * price.output
    )
    return total / 1_000_000
