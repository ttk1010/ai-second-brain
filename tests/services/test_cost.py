"""Tests for the usage-based cost estimate (Issue #35)."""

import pytest

from backend.models.usage import UsageRecord
from backend.services.cost import TokenPrices, UnknownPriceError, estimate_cost

PRICES = {
    "text-model": TokenPrices(input=2.0, cached_input=0.5, output=10.0),
    "image-model": TokenPrices(input=5.0, cached_input=1.0, output=30.0, image_input=8.0),
}


def test_text_cost_bills_cached_input_at_its_own_rate() -> None:
    record = UsageRecord(
        kind="text",
        model="text-model",
        operation="complete",
        input_tokens=1_000_000,
        output_tokens=100_000,
        cached_input_tokens=400_000,
    )
    # 600k plain * $2 + 400k cached * $0.5 + 100k out * $10 (per 1M)
    assert estimate_cost(record, PRICES) == pytest.approx(1.2 + 0.2 + 1.0)


def test_image_cost_separates_text_and_image_input() -> None:
    record = UsageRecord(
        kind="image",
        model="image-model",
        operation="edit",
        input_tokens=1_000,
        output_tokens=10_000,
        input_image_tokens=800,
    )
    # 200 text * $5 + 800 image * $8 + 10k out * $30 (per 1M)
    assert estimate_cost(record, PRICES) == pytest.approx((1_000 + 6_400 + 300_000) / 1e6)


def test_unknown_model_fails_loudly() -> None:
    record = UsageRecord(
        kind="text", model="nope", operation="complete", input_tokens=1, output_tokens=1
    )
    with pytest.raises(UnknownPriceError):
        estimate_cost(record, PRICES)


def test_default_prices_cover_the_compared_models() -> None:
    """The snapshot must price every model the measurement script compares."""
    for model in ("gpt-5.4", "gpt-image-2", "gpt-image-2.5-flare"):
        record = UsageRecord(
            kind="image", model=model, operation="generate", input_tokens=10, output_tokens=10
        )
        assert estimate_cost(record) > 0
