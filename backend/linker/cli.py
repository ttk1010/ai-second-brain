"""``asb-link`` — deterministic linking commands for the relink skill (Issue #22).

Two subcommands the Claude Code relink skill (Issue #23) drives:

- ``index`` prints every note's structured data as JSON, so Claude can reason
  about which notes are related.
- ``apply`` writes the chosen links into one note's Related Notes section,
  safely and idempotently.

No LLM is involved: judgment lives in the skill, mechanism lives here.
"""

import argparse
import json
import sys
from pathlib import Path

from backend.config import DEFAULT_SETTINGS_PATH, SettingsError, load_settings
from backend.linker.index import VaultIndex
from backend.linker.related import RelatedLink, update_related_section


def main(argv: list[str] | None = None) -> int:
    """Run the linker CLI. Returns a process exit code."""
    args = _parse_args(argv)
    if args.command == "index":
        return _run_index(args)
    if args.command == "apply":
        return _run_apply(args)
    return 2  # pragma: no cover - argparse enforces a valid command


def _run_index(args: argparse.Namespace) -> int:
    vault_path = _resolve_vault(args)
    if vault_path is None:
        return 2
    index = VaultIndex.build(vault_path)
    json.dump(index.to_list(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def _run_apply(args: argparse.Namespace) -> int:
    note_path = Path(args.note)
    if not note_path.is_file():
        print(f"Note not found: {note_path}", file=sys.stderr)
        return 2

    links = [RelatedLink.parse(value) for value in (args.link or [])]
    original = note_path.read_text(encoding="utf-8")
    updated = update_related_section(original, links)
    if updated != original:
        note_path.write_text(updated, encoding="utf-8")
        print(f"Updated Related Notes: {note_path}")
    else:
        print(f"No change: {note_path}")
    return 0


def _resolve_vault(args: argparse.Namespace) -> Path | None:
    if args.vault is not None:
        return Path(args.vault)
    try:
        return load_settings(args.config).vault_path
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return None


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="asb-link",
        description="Index the Vault and update notes' Related Notes sections.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    index_p = sub.add_parser("index", help="Print all notes as JSON.")
    index_p.add_argument("--vault", type=Path, default=None, help="Vault path (overrides config).")
    index_p.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_SETTINGS_PATH,
        help=f"Settings TOML (default: {DEFAULT_SETTINGS_PATH}).",
    )

    apply_p = sub.add_parser("apply", help="Set a note's Related Notes links.")
    apply_p.add_argument("note", help="Path to the note file to update.")
    apply_p.add_argument(
        "--link",
        action="append",
        metavar="TITLE[:RELATIONSHIP]",
        help="A related note title, optionally with a relationship type. Repeatable.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
