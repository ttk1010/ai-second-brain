"""``asb-inbox`` — process the Vault's 00 Inbox queue into notes (Phase 4).

Run manually or on a schedule (cron/launchd). Capture happens anywhere (Obsidian
mobile, a share shortcut) by dropping a stub into ``00 Inbox/``; this command
turns those stubs into full notes when the machine is on (ADR 0006).
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from backend.config import DEFAULT_SETTINGS_PATH, SettingsError, load_settings
from backend.inbox.worker import InboxWorker
from backend.services import build_pipeline
from backend.storage.paths import INBOX_FOLDER


def main(argv: list[str] | None = None) -> int:
    """Run the inbox worker. Returns a process exit code."""
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load_dotenv()

    try:
        settings = load_settings(args.config)
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    pipeline = build_pipeline(settings, no_image=args.no_image)
    inbox_dir = settings.vault_path / INBOX_FOLDER
    summary = InboxWorker(pipeline, inbox_dir, overwrite=args.overwrite).process_all()

    print(
        f"Inbox: {summary.created} created, {summary.skipped} existing, "
        f"{summary.unsupported} unsupported, {summary.failed} failed."
    )
    return 0 if summary.failed == 0 else 1


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="asb-inbox",
        description="Process URL/concept stubs in the Vault's 00 Inbox into notes.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate even if a note already exists.",
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
