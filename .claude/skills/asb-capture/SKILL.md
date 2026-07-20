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
   - If the message adds a **style/audience/emphasis instruction** (e.g. "高校生向けに",
     "歴史的背景を含めて", "発行モデルの違いを主軸に"), pass it separately via
     `--guidance "<その指示>"`. Keep the concept/URL/items as the input, and put the
     "how to write it" part in `--guidance`. It steers the body and the illustration.
   - Add `--no-image` to skip the illustration (saves cost).
   - Add `--overwrite` only if the user explicitly wants to regenerate an
     existing note (e.g. to re-run with different `--guidance`).
3. Report back concisely: the created note path, or that it already existed, or
   the error. Keep replies short — they may be read in a chat app.

## Notes

- `asb` writes to the configured external Vault. Concept input generates an
  explanation + illustration; a URL fetches and summarizes the article.
- For **login-required** pages `asb` cannot fetch (the fetch fails or returns
  only a members-only teaser), use captured content: obtain the article **body
  text**, save it to a file, and run
  `uv run python -m backend.cli --captured-from "<URL>" --text-file <path> --title "<title>"`.
  Get the body text either from the message itself, by reading the page through
  the user's logged-in browser (Claude in Chrome tools — open the URL in a
  session tab; login cookies carry over), or by asking the user to paste it.
  Never enter credentials or bypass any wall. Full guide:
  `docs/CAPTURED_CONTENT.md`.
- Generation calls OpenAI (per-note cost). Idempotent: an existing concept/URL is
  skipped, not regenerated (no extra cost).
- If several items were dropped into the Vault's `00 Inbox/`, run
  `uv run asb-inbox` instead of one `asb` per item.
- This skill runs `asb`; it does not edit notes directly.
