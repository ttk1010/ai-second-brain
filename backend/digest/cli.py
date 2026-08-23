"""``asb-digest`` — build a monthly AI-news digest note + illustration (Issue #39/#40).

Reads ledge.ai's 30-day access ranking and writes a digest note (ranked stories +
one-line summaries + overview) with one overview illustration under ``08 Digests``.

Three modes:
- ``asb-digest`` (no subcommand): fully automatic — OpenAI writes the summaries and
  the image. Good for unattended cron/launchd runs (ADR 0006).
- ``asb-digest fetch``: print the ranking + each article's body as JSON, using no
  OpenAI. The Claude-Code digest skill reads this and authors better labels from
  the bodies (no OpenAI text cost).
- ``asb-digest build --from FILE``: build the note + illustration from the skill's
  authored JSON (image is the only OpenAI cost).

The ranking is always the last 30 days; ``--month`` only labels the note (its
idempotency key), defaulting to the current month.
"""

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from backend.config import DEFAULT_SETTINGS_PATH, SettingsError, load_settings
from backend.parser import (
    DigestExtraction,
    HttpArticleFetcher,
    LedgeAiRankingFetcher,
    RankedArticle,
)
from backend.parser.fetcher import FetchError
from backend.services import build_pipeline
from backend.storage.git import commit_note

_BODY_CHARS_DEFAULT = 1500


def main(argv: list[str] | None = None) -> int:
    """Run the digest command. Returns a process exit code."""
    args = sys.argv[1:] if argv is None else argv
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args and args[0] == "fetch":
        return _fetch(args[1:])
    if args and args[0] == "build":
        return _build(args[1:])
    return _auto(args)


def _auto(argv: list[str]) -> int:
    """Fully automatic digest (OpenAI writes summaries + image)."""
    args = _auto_parser().parse_args(argv)
    load_dotenv()
    try:
        settings = load_settings(args.config)
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    period = args.month or date.today().strftime("%Y-%m")
    pipeline = build_pipeline(settings, no_image=args.no_image)
    try:
        result = pipeline.run_digest(period, top=args.top, overwrite=args.overwrite)
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the user
        print(f"Failed to build digest: {exc}", file=sys.stderr)
        return 1
    return _report(result, settings)


def _fetch(argv: list[str]) -> int:
    """Print the ranking + article bodies as JSON (no OpenAI)."""
    parser = argparse.ArgumentParser(prog="asb-digest fetch")
    parser.add_argument("--top", type=int, default=10, metavar="N")
    parser.add_argument("--month", default="", metavar="YYYY-MM")
    parser.add_argument("--chars", type=int, default=_BODY_CHARS_DEFAULT, metavar="N")
    args = parser.parse_args(argv)

    period = args.month or date.today().strftime("%Y-%m")
    try:
        ranked = LedgeAiRankingFetcher().fetch_monthly(limit=args.top)
    except FetchError as exc:
        print(f"Failed to fetch the ranking: {exc}", file=sys.stderr)
        return 1
    if not ranked:
        print(
            "Could not read the access ranking (site structure may have changed).", file=sys.stderr
        )
        return 1

    fetcher = HttpArticleFetcher()
    articles = []
    for item in ranked:
        try:
            body = fetcher.fetch(item.url).text[: args.chars]
        except FetchError:
            body = ""
        articles.append({"rank": item.rank, "title": item.title, "url": item.url, "body": body})

    print(json.dumps({"period": period, "top": args.top, "articles": articles}, ensure_ascii=False))
    return 0


def _build(argv: list[str]) -> int:
    """Build the note + illustration from the skill's authored JSON."""
    parser = argparse.ArgumentParser(prog="asb-digest build")
    parser.add_argument("--from", dest="source", type=Path, required=True, metavar="FILE")
    parser.add_argument("--month", default="", metavar="YYYY-MM")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-image", action="store_true")
    parser.add_argument("--config", type=Path, default=DEFAULT_SETTINGS_PATH)
    args = parser.parse_args(argv)
    load_dotenv()

    try:
        settings = load_settings(args.config)
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        data = json.loads(args.source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Input error: could not read authored digest JSON: {exc}", file=sys.stderr)
        return 2

    period = args.month or str(data.get("period") or "").strip()
    ranked, extraction = _authored(data)
    if not period or not ranked:
        print("Input error: digest JSON needs a period and at least one item.", file=sys.stderr)
        return 2

    pipeline = build_pipeline(settings, no_image=args.no_image)
    try:
        result = pipeline.render_digest(
            period, ranked, extraction, top=len(ranked), overwrite=args.overwrite
        )
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the user
        print(f"Failed to build digest: {exc}", file=sys.stderr)
        return 1
    return _report(result, settings)


def _authored(data: dict) -> tuple[list[RankedArticle], DigestExtraction]:
    """Turn the skill's authored JSON into ranked articles + a DigestExtraction."""
    ranked: list[RankedArticle] = []
    summaries: dict[int, str] = {}
    labels: dict[int, str] = {}
    for item in data.get("items") or []:
        if not isinstance(item, dict):
            continue
        try:
            rank = int(item.get("rank"))
        except (TypeError, ValueError):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        if not (rank and title and url):
            continue
        ranked.append(RankedArticle(rank=rank, title=title, url=url))
        if str(item.get("summary") or "").strip():
            summaries[rank] = item["summary"].strip()
        if str(item.get("label") or "").strip():
            labels[rank] = item["label"].strip()
    extraction = DigestExtraction(
        overview=str(data.get("overview") or "").strip(),
        summaries=summaries,
        labels=labels,
        concepts=[str(c).strip() for c in (data.get("concepts") or []) if str(c).strip()],
        entities=[str(e).strip() for e in (data.get("entities") or []) if str(e).strip()],
    )
    return ranked, extraction


def _report(result, settings) -> int:
    print(result.message)
    if result.status == "created" and settings.auto_commit and result.path is not None:
        if commit_note(
            settings.vault_path, result.path, f"Add digest: {result.knowledge_object.title}"
        ):
            print("Committed to Vault Git repository.")
    return 0


def _auto_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asb-digest",
        description="Build a monthly AI-news digest from ledge.ai's 30-day access ranking.",
    )
    parser.add_argument(
        "--month", default="", metavar="YYYY-MM", help="Label (default: this month)."
    )
    parser.add_argument("--top", type=int, default=10, metavar="N", help="How many stories.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate if it exists.")
    parser.add_argument("--no-image", action="store_true", help="Skip the illustration.")
    parser.add_argument("--config", type=Path, default=DEFAULT_SETTINGS_PATH)
    return parser


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
