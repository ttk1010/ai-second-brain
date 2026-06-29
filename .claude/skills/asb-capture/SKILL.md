---
name: asb-capture
description: >-
  Capture an AI concept or article URL into the AI Second Brain Obsidian Vault by
  running `asb`. Use when a message contains a concept/keyword or an article URL
  to save to the second brain — especially via Claude Code Channels (Telegram),
  where you act on incoming messages. Generation uses the usual per-note OpenAI
  cost; an existing note is skipped.
---

# Capture into AI Second Brain

When the user (or an incoming Channels message) gives you an AI **concept** or an
**article URL** to save, turn it into a note by running `asb`.

## Steps

1. Identify the input: the concept text (e.g. `Transformer`), the URL, or — if the
   message asks to **compare** several things — the list of items.
2. From the repo root, run:

   ```bash
   uv run python -m backend.cli "<input>"
   ```

   - For a comparison request (e.g. "compare Claude, GPT and Gemini"), extract the
     items and run `uv run python -m backend.cli --compare "Claude, GPT, Gemini"` instead.
     The note is saved under `04 Comparisons/` with a comparison table.
   - Add `--no-image` to skip the illustration (saves cost).
   - Add `--overwrite` only if the user explicitly wants to regenerate an
     existing note.
3. Report back concisely: the created note path, or that it already existed, or
   the error. Keep replies short — they may be read in a chat app.

## Notes

- `asb` writes to the configured external Vault. Concept input generates an
  explanation + illustration; a URL fetches and summarizes the article.
- Generation calls OpenAI (per-note cost). Idempotent: an existing concept/URL is
  skipped, not regenerated (no extra cost).
- If several items were dropped into the Vault's `00 Inbox/`, run
  `uv run asb-inbox` instead of one `asb` per item.
- This skill runs `asb`; it does not edit notes directly.
