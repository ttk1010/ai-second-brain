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
from backend.llm import OpenAIProvider
from backend.markdown import MarkdownGenerator
from backend.parser import ConceptExtractor, KnowledgeObjectBuilder
from backend.services import KnowledgePipeline
from backend.storage import VaultWriter
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

    provider = OpenAIProvider(model=settings.llm_model)
    pipeline = KnowledgePipeline(
        extractor=ConceptExtractor(provider),
        builder=KnowledgeObjectBuilder(),
        markdown_generator=MarkdownGenerator(),
        vault_writer=VaultWriter(settings.vault_path),
        language=settings.default_language,
    )

    try:
        result = pipeline.run(args.input, overwrite=args.overwrite)
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the user
        print(f"Failed to generate note: {exc}", file=sys.stderr)
        return 1

    if result.status == "unsupported":
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
        description="Turn an AI concept into a structured note in your Obsidian Vault.",
    )
    parser.add_argument("input", help="An AI concept (e.g. 'Transformer') or URL.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing note instead of creating a numbered copy.",
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
