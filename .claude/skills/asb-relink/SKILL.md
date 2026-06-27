---
name: asb-relink
description: >-
  Connect the AI Second Brain knowledge notes to each other. Reads every note in
  the Obsidian Vault, decides which notes are related (and how), and updates each
  note's "Related Notes" section to link the genuinely related existing notes.
  Use when the user wants to relink the vault, connect their notes, refresh
  related notes / backlinks, or organize the knowledge graph. Runs under the
  Claude subscription and uses no OpenAI API (no extra cost).
---

# Relink the AI Second Brain vault

You connect accumulated knowledge notes so the vault becomes a graph instead of a
pile of isolated notes. The *judgment* (which notes relate, and how) is yours;
the *writing* is done by a deterministic, safe command so notes are never
corrupted. Re-running is safe and idempotent.

## Cost

This skill uses your reasoning only — it does **not** call the OpenAI API, so it
adds no per-run cost beyond your existing Claude subscription. Never call any
paid API from this skill.

## Steps

1. **Read the vault index.** Run from the repo root:

   ```bash
   uv run asb-link index
   ```

   This prints a JSON array of every note: `title`, `path` (Vault-relative),
   `tags`, `source_type`, `id`. (If the console script fails, use
   `uv run python -m backend.linker.cli index`.)

2. **Find the Vault path.** Read `vault_path` from `config/settings.toml`. You
   will join it with each note's `path` to get an absolute path for step 4.

3. **Decide the links.** For each note, choose the *other existing* notes it is
   genuinely related to, using their **exact titles from the index**. Judge
   relatedness from shared tags/topics and your own knowledge — including near
   synonyms and spelling variants the deterministic layer would miss.

   - Only link notes that **exist in the index**. Never invent titles or create
     dangling links.
   - Be selective: link the few most relevant notes (roughly 2–6), not everything
     that is loosely on-topic. Over-linking makes the graph noisy.
   - You do **not** need to add reverse links — Obsidian shows backlinks
     automatically from the forward links.
   - When the relationship is clear, tag it with one of: `prerequisite`,
     `related`, `successor`, `alternative`, `implementation`, `application`,
     `regulation`. When unsure, omit the type (it defaults to a plain link).

4. **Apply the links per note.** For each note that has related notes:

   ```bash
   uv run asb-link apply "<vault_path>/<note path>" \
     --link "Other Note:prerequisite" \
     --link "Another Note"
   ```

   `apply` rewrites **only** that note's "Related Notes" section; everything else
   (frontmatter, summary, illustration, references, tags) is left untouched, and
   re-running with the same links is a no-op. A note with no good matches can be
   left as-is.

5. **Summarize.** Report how many notes you linked and any notes left unlinked
   (e.g. too few notes yet to relate to).

## Notes

- The value grows with the vault: with only a couple of notes there is little to
  connect; run this again as the vault grows.
- This skill never deletes notes or edits sections other than "Related Notes".
