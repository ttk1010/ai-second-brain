"""Command-line entry point for AI Second Brain.

Usage:
    asb "Transformer"
    asb "MCP" --overwrite

Reads configuration from config/settings.toml and the OpenAI API key from the
environment (a local .env file is loaded automatically). The key is never
printed.
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from backend.config import DEFAULT_SETTINGS_PATH, SettingsError, load_settings
from backend.services import build_pipeline
from backend.storage.git import commit_note


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns a process exit code."""
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load_dotenv()

    try:
        settings = load_settings(args.config)
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    pipeline = build_pipeline(settings, no_image=args.no_image)

    # --compare is sugar: normalize to the canonical "compare:" form so there is
    # a single classification path (ADR 0007).
    raw_input = args.input
    if args.compare and not raw_input.lower().startswith("compare:"):
        raw_input = f"compare: {raw_input}"

    try:
        result = pipeline.run(raw_input, overwrite=args.overwrite, guidance=args.guidance)
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the user
        print(f"Failed to generate note: {exc}", file=sys.stderr)
        return 1

    if result.status in ("unsupported", "exists"):
        print(result.message)
        return 0

    print(result.message)
    if settings.auto_commit and result.path is not None:
        committed = commit_note(
            settings.vault_path, result.path, f"Add note: {result.knowledge_object.title}"
        )
        if committed:
            print("Committed to Vault Git repository.")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="asb",
        description="Turn an AI concept or article URL into a structured Obsidian note.",
    )
    parser.add_argument("input", help="An AI concept (e.g. 'Transformer') or URL.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate and replace an existing note instead of skipping it.",
    )
    parser.add_argument(
        "--no-image",
        action="store_true",
        help="Skip illustration generation (saves cost; the note is still created).",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Treat the input as a list of items to compare (e.g. 'GPT, Claude, Gemini').",
    )
    parser.add_argument(
        "--guidance",
        default="",
        metavar="TEXT",
        help=(
            "Free-text instruction to steer this note's tone, audience, and emphasis "
            "(e.g. '高校生向けに、歴史的背景を含めて'). Applies to the body and the "
            "illustration. Recorded in the note's frontmatter."
        ),
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
