"""Measure per-note cost and compare image models (Issues #35, #45).

For each case the text (extraction + Educational Plan) is generated once, then
the same Knowledge Object is illustrated by every configured model and quality,
so the comparison isolates the image model. Everything is written to a
throwaway Vault under ``--out``; the real Vault is never touched.

Usage (from the repository root):

    uv run python scripts/measure_generation.py --check              # free
    uv run python scripts/measure_generation.py --out DIR            # show the plan
    uv run python scripts/measure_generation.py --out DIR --yes      # billable run

Outputs ``DIR/results.json`` (raw usage per call) and ``DIR/summary.md``.
"""

import argparse
import json
import logging
import sys
import tomllib
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from backend.config import Settings, load_settings
from backend.image import ImageError, OpenAIImageProvider
from backend.models import ImageQuality, KnowledgeObject
from backend.models.usage import UsageRecord, UsageRecorder
from backend.services.cost import PRICES_AS_OF, UnknownPriceError, estimate_cost
from backend.services.factory import build_pipeline
from backend.storage import IllustrationWriter

logger = logging.getLogger("measure")

DEFAULT_CASES = Path(__file__).with_name("image_model_comparison.toml")


@dataclass(frozen=True)
class Case:
    name: str
    input: str
    qualities: list[str]
    pages: int | None = None


@dataclass
class Collector:
    """Collects usage records tagged with where in the run they happened."""

    rows: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    def recorder(self, **context: str) -> UsageRecorder:
        def record(usage: UsageRecord) -> None:
            try:
                cost = estimate_cost(usage)
            except UnknownPriceError:
                cost = None
            self.rows.append({**context, **asdict(usage), "cost_usd": cost})

        return record


def load_cases(path: Path) -> tuple[list[str], list[Case]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    default_qualities = data.get("default_qualities", ["medium"])
    cases = [
        Case(
            name=c["name"],
            input=c["input"],
            qualities=c.get("qualities", default_qualities),
            pages=c.get("pages"),
        )
        for c in data["cases"]
    ]
    for case in cases:
        for quality in case.qualities:
            ImageQuality(quality)  # fail fast on a typo, before any billing
    return data["models"], cases


def check_models(settings: Settings, models: list[str]) -> bool:
    """Confirm every model is available to this API key (free: no generation)."""
    from openai import OpenAI

    client = OpenAI()
    ok = True
    for model in [settings.llm_model, *models]:
        try:
            client.models.retrieve(model)
            print(f"  ok       {model}")
        except Exception as exc:  # the SDK raises many error subclasses
            ok = False
            print(f"  missing  {model}: {exc}")
    return ok


def print_plan(models: list[str], cases: list[Case]) -> None:
    images = 0
    for case in cases:
        pages = case.pages or 1
        count = pages * len(models) * len(case.qualities)
        images += count
        print(f"  {case.name:<28} text x1, images x{count} ({'/'.join(case.qualities)})")
    print(f"  total: {len(cases)} text runs, ~{images} images (pages depend on the planner)")


def run_case(
    case: Case, models: list[str], settings: Settings, out: Path, collector: Collector
) -> None:
    case_dir = out / case.name
    text_settings = settings.model_copy(update={"vault_path": case_dir / "text"})
    (case_dir / "text").mkdir(parents=True, exist_ok=True)

    logger.info("== %s: text (%s)", case.name, case.input)
    pipeline = build_pipeline(
        text_settings,
        no_image=True,
        usage_recorder=collector.recorder(case=case.name, stage="text"),
    )
    result = pipeline.run(case.input, pages=case.pages, overwrite=True)
    if result.status != "created" or result.knowledge_object is None:
        collector.errors.append({"case": case.name, "stage": "text", "error": result.message})
        logger.error("%s: text generation failed: %s", case.name, result.message)
        return

    for model in models:
        for quality in case.qualities:
            illustrate(result.knowledge_object, case, model, quality, settings, case_dir, collector)


def illustrate(
    ko: KnowledgeObject,
    case: Case,
    model: str,
    quality: str,
    settings: Settings,
    case_dir: Path,
    collector: Collector,
) -> None:
    variant = f"{model}-{quality}"
    logger.info("== %s: %s", case.name, variant)
    provider = OpenAIImageProvider(
        model=model,
        usage_recorder=collector.recorder(
            case=case.name, stage="image", image_model=model, quality=quality
        ),
    )
    writer = IllustrationWriter(
        case_dir / variant,
        provider,
        image_output_dir="Images",
        quality=ImageQuality(quality),
        default_aspect_ratio=settings.default_aspect_ratio,
    )
    try:
        writer.write(ko.model_copy(deep=True), overwrite=True)
    except ImageError as exc:
        collector.errors.append({"case": case.name, "stage": variant, "error": str(exc)})
        logger.error("%s: %s failed: %s", case.name, variant, exc)


def summarize(collector: Collector) -> str:
    def money(value: float | None) -> str:
        return "n/a" if value is None else f"${value:.4f}"

    def total(rows: list[dict]) -> float | None:
        costs = [r["cost_usd"] for r in rows]
        return None if any(c is None for c in costs) else sum(costs)

    lines = [f"# Measurement summary (prices as of {PRICES_AS_OF})", ""]

    lines += ["## Text per case", "", "| case | calls | in | out | seconds | cost |"]
    lines.append("|---|---:|---:|---:|---:|---:|")
    by_case: dict[str, list[dict]] = defaultdict(list)
    for row in collector.rows:
        if row["stage"] == "text":
            by_case[row["case"]].append(row)
    for case, rows in by_case.items():
        lines.append(
            f"| {case} | {len(rows)} | {sum(r['input_tokens'] for r in rows)} "
            f"| {sum(r['output_tokens'] for r in rows)} "
            f"| {sum(r['elapsed_seconds'] for r in rows):.1f} | {money(total(rows))} |"
        )

    lines += ["", "## Images per case", ""]
    lines.append("| case | model | quality | images | sec/image | out tokens | cost |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    by_variant: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in collector.rows:
        if row["stage"] == "image":
            by_variant[(row["case"], row["image_model"], row["quality"])].append(row)
    for (case, model, quality), rows in by_variant.items():
        seconds = sum(r["elapsed_seconds"] for r in rows) / len(rows)
        lines.append(
            f"| {case} | {model} | {quality} | {len(rows)} | {seconds:.1f} "
            f"| {sum(r['output_tokens'] for r in rows)} | {money(total(rows))} |"
        )

    if collector.errors:
        lines += ["", "## Errors", ""]
        lines += [f"- {e['case']} / {e['stage']}: {e['error']}" for e in collector.errors]

    lines += ["", f"Total estimated cost: {money(total(collector.rows))}", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--settings", type=Path, default=Path("config/settings.toml"))
    parser.add_argument("--out", type=Path, help="Output directory (outside the real Vault).")
    parser.add_argument("--only", nargs="+", help="Run only these case names.")
    parser.add_argument("--check", action="store_true", help="Check model access (free).")
    parser.add_argument("--yes", action="store_true", help="Actually call the API (billable).")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load_dotenv()
    settings = load_settings(args.settings)
    models, cases = load_cases(args.cases)
    if args.only:
        cases = [c for c in cases if c.name in args.only]

    if args.check:
        return 0 if check_models(settings, models) else 1

    if args.out is None:
        parser.error("--out is required unless --check is given.")
    out = args.out.expanduser().resolve()
    if out.is_relative_to(settings.vault_path.resolve()):
        parser.error("--out must not be inside the real Vault.")

    print("Planned run:")
    print_plan(models, cases)
    if not args.yes:
        print("\nDry run only. Re-run with --yes to call the API (billable).")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    collector = Collector()
    for case in cases:
        run_case(case, models, settings, out, collector)

    results = {"prices_as_of": PRICES_AS_OF, "rows": collector.rows, "errors": collector.errors}
    (out / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = summarize(collector)
    (out / "summary.md").write_text(summary, encoding="utf-8")
    print("\n" + summary)
    return 1 if collector.errors else 0


if __name__ == "__main__":
    sys.exit(main())
