---
name: asb-digest
description: >-
  Build the monthly AI-news digest for AI Second Brain by reading the actual
  article bodies. Fetches ledge.ai's 30-day access ranking plus each article's
  text, then you write an accurate short label + one-line summary per story and an
  overall overview, and a helper renders the digest note + one overview
  illustration. Use when the user wants the monthly digest, "今月のまとめ", a
  top-10 AI news image, or a higher-quality digest than the fully-automatic
  `asb-digest`. Your text authoring runs under the Claude subscription (no OpenAI
  text cost); only the illustration uses the OpenAI image API.
---

# Build the monthly AI-news digest (body-informed)

You turn the month's most-read AI news into one digest note + overview
illustration. The *labels and summaries* are yours to write **from the article
bodies** so they capture each story's key terms; the *building* is done by a
deterministic helper.

## Cost

Your reading and writing use the Claude subscription — **no OpenAI text cost**.
The only paid step is the illustration (gpt-image-2), generated once per run. Pass
`--no-image` to `build` to skip it entirely (no OpenAI cost at all).

## Steps

1. **Fetch the ranking + article bodies.** From the repo root:

   ```bash
   uv run python -m backend.digest.cli fetch --top 10
   ```

   This prints JSON: `{"period": "YYYY-MM", "top": N, "articles": [{"rank",
   "title", "url", "body"}]}`. It uses no OpenAI. (If a body is empty, the fetch
   failed for that URL — fall back to its title.)

2. **Read each body and author the digest.** For every article, write:
   - `label`: a short caption for the illustration tile, ~8-16 characters,
     **complete** (never cut a word; close any 「」). It **must keep at least one
     of the story's key identifying terms** — the specific product/model/org or
     the core topic (e.g. keep "ヤコビアン予想" or "Fable 5", not a vague
     "反例提示").
   - `summary`: one accurate factual sentence (this is the readable text in the
     note).

   Also write an overall `overview` (2-3 sentences on the month's themes), and
   `concepts` / `entities` (recurring topics and notable orgs/models/people).
   Keep the same language as the articles (Japanese by default).

3. **Write your authored JSON** to a temp file, in this shape:

   ```json
   {
     "period": "2026-08",
     "overview": "…",
     "concepts": ["…"],
     "entities": ["…"],
     "items": [
       {"rank": 1, "title": "<original title>", "url": "<original url>",
        "label": "…", "summary": "…"}
     ]
   }
   ```

   Keep each item's original `title` and `url` from step 1; add your `label` and
   `summary`. Include every ranked item.

4. **Build the note + illustration.**

   ```bash
   uv run python -m backend.digest.cli build --from <your.json>
   ```

   Add `--no-image` to skip the illustration, `--overwrite` to replace an existing
   month's digest, `--month YYYY-MM` to override the label.

5. **Report** the created note path (or that it already existed), concisely.

## Notes

- The note is saved under `08 Digests/`; the illustration under `Images/`. The
  digest is idempotent on its `period` — the same month is skipped unless you pass
  `--overwrite`.
- The image carries only the short labels; the accurate one-line summaries live in
  the note (generated-image text is unreliable — ADR 0010).
- Prefer this skill for quality; the fully-automatic `uv run asb-digest` (OpenAI
  writes the text) stays available for unattended cron/launchd runs.
- If `asb-digest` as a console script fails with `ModuleNotFoundError: backend`,
  use the `python -m backend.digest.cli …` form shown above.
