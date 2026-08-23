"""``asb-digest`` — build a monthly AI-news digest note + illustration (Issue #39).

Reads ledge.ai's 30-day access ranking, summarizes each headline in one line, and
writes a digest note (with one overview illustration) under ``08 Digests``. Run
manually or monthly from cron/launchd (ADR 0006 — no resident daemon).

The ranking is always the last 30 days; ``--month`` only labels the note (and is
its idempotency key), defaulting to the current month.
"""

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from backend.config import DEFAULT_SETTINGS_PATH, SettingsError, load_settings
from backend.services import build_pipeline
from backend.storage.git import commit_note


def main(argv: list[str] | None = None) -> int:
    """Run the digest command. Returns a process exit code."""
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
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

    print(result.message)
    if result.status == "created" and settings.auto_commit and result.path is not None:
        if commit_note(
            settings.vault_path, result.path, f"Add digest: {result.knowledge_object.title}"
        ):
            print("Committed to Vault Git repository.")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="asb-digest",
        description="Build a monthly AI-news digest from ledge.ai's 30-day access ranking.",
    )
    parser.add_argument(
        "--month",
        default="",
        metavar="YYYY-MM",
        help="Label/idempotency key for the note (default: current month).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="How many ranked stories to include (default: 10).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate even if this month's digest already exists.",
    )
    parser.add_argument(
        "--no-image",
        action="store_true",
        help="Skip illustration generation (saves cost).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_SETTINGS_PATH,
        help=f"Path to the settings TOML (default: {DEFAULT_SETTINGS_PATH}).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
