"""``asb-revise`` — improve one part of an existing note (Issue #29).

Rewrites a body section (Summary / Background / Key Takeaways) or redraws the
illustration from a natural-language instruction, without regenerating the whole
note. The target is inferred from the instruction unless ``--section`` or
``--illustration`` forces it. Writes in place (the Vault is Git-managed).

Usage:
    asb-revise "Transformer" "要約をもっと易しく"
    asb-revise "AWS" "図を白背景で描き直して" --illustration
    asb-revise "AWS" "背景を厚く" --section background
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from backend.config import DEFAULT_SETTINGS_PATH, SettingsError, load_settings
from backend.services import build_reviser
from backend.storage.git import commit_note


def main(argv: list[str] | None = None) -> int:
    """Run the reviser CLI. Returns a process exit code."""
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load_dotenv()

    try:
        settings = load_settings(args.config)
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    reviser = build_reviser(settings, no_image=args.no_image)

    try:
        result = reviser.revise(
            args.reference,
            args.instruction,
            section=args.section,
            illustration=args.illustration,
        )
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the user
        print(f"Failed to revise note: {exc}", file=sys.stderr)
        return 1

    print(result.message)
    if result.status != "revised":
        # not_found / unsupported are reported, not treated as a crash.
        return 0

    if settings.auto_commit and result.path is not None:
        if commit_note(settings.vault_path, result.path, f"Revise note: {result.path.stem}"):
            print("Committed to Vault Git repository.")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="asb-revise",
        description="Revise a section or the illustration of an existing note.",
    )
    parser.add_argument("reference", help="The note to revise (its title or filename).")
    parser.add_argument("instruction", help="What to change, in natural language.")
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--section",
        metavar="NAME",
        help="Force the target section (summary / background / key_takeaways).",
    )
    target.add_argument(
        "--illustration",
        action="store_true",
        help="Force revising the illustration instead of a text section.",
    )
    parser.add_argument(
        "--no-image",
        action="store_true",
        help="Do not build the image provider (text-section revisions only).",
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
