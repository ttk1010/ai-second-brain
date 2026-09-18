# AI Second Brain

> Capture. Understand. Visualize. Remember.

**English** · [日本語 (README.ja.md)](README.ja.md)

[![CI](https://github.com/ttk1010/ai-second-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/ttk1010/ai-second-brain/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

<p align="center">
  <img src="docs/assets/cover.png" width="820"
       alt="Send input from anywhere — the CLI, the Claude mobile app, or Telegram — and AI Second Brain turns it into a structured Markdown note, an educational illustration, and an Obsidian-style graph of linked notes.">
</p>

<p align="center"><sub>Cover illustration generated with AI Second Brain's image engine (gpt-image-2).</sub></p>

## What is this?

AI Second Brain turns what you learn into a **structured, visual, and
continuously evolving knowledge base**. Give it a concept (`Transformer`), an
article URL, or a comparison (`GPT, Claude, Gemini`) — it generates a structured,
illustrated Markdown note in your [Obsidian](https://obsidian.md/) vault and
links it into your knowledge graph. AI is its default focus, but it handles any
field of knowledge (biology, economics, cooking…), tagging each note with its
domain (ADR 0008).

The real product isn't notes or images; it's **organized, reusable knowledge**.
Every output is generated from a single canonical [Knowledge
Object](docs/DATA_MODEL.md), so notes stay consistent and the vault remains
valuable even without AI tools.

> 📖 The README is in English and Japanese; the detailed design docs
> (`docs/`, ADRs) are written in **Japanese**.

## Example

```bash
uv run asb "LLM"
```

produces a note like `01 Concepts/Large Language Model.md` in your vault — a full
note with an embedded illustration and resolved links:

```markdown
---
title: "Large Language Model"
source_type: concept
tags: [Transformer, Generative AI, Foundation Model, RAG, Attention, ...]
---

# Large Language Model

## Summary
A large language model (LLM) is an AI model trained on massive amounts of text to
predict and generate natural-language patterns…

## Illustration
![[Images/LLM.png]]

## Key Takeaways
- An LLM learns statistical patterns of language from large corpora and predicts
  the next token…
- It is highly general: prompting or fine-tuning adapts it to many tasks…

## Related Notes
- [[AI Agent]] — application
- [[RAG]] — application
- [[Embeddings]] — related
```

(Notes are generated in the language you configure; the default is Japanese —
see [README.ja.md](README.ja.md) for a Japanese example.)

## Requirements

- **Python 3.12** and [uv](https://docs.astral.sh/uv/).
- **An OpenAI API key — required.** Generating a note calls the OpenAI API (text
  with `gpt-5.4`, illustrations with `gpt-image-2`), so it is **billable per
  note**. Image generation is the dominant cost — re-running the same input is
  skipped (no re-charge), and `--no-image` skips the illustration to save cost.
- **A Claude subscription + [Claude Code](https://www.claude.com/product/claude-code) — optional.**
  Only needed for the `asb-relink` linking skill and Telegram capture (Claude
  Code Channels); the core `asb` commands do not require it.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12 (see Requirements above).

```bash
# 1. Install dependencies
uv sync --dev

# 2. Configure: point vault_path at your Obsidian vault, set your API key
cp config/settings.example.toml config/settings.toml   # then edit vault_path
echo 'OPENAI_API_KEY=sk-...' > .env

# 3. Generate a note
uv run asb "Transformer"                 # a concept
uv run asb "https://ledge.ai/..."        # a news article
uv run asb --compare "GPT, Claude, Gemini"   # a comparison

# Steer tone / audience / emphasis with --guidance
uv run asb "Transformer" --guidance "For high-schoolers; include the history"

# Explain across several illustration pages instead of one image
uv run asb "Transformer" --pages 4      # exactly 4 facet pages
uv run asb "Transformer" --pages auto   # let the planner choose (2–6)
```

Each note is written into your vault with an educational illustration. Re-running
the same input is a no-op (use `--overwrite` to regenerate, `--no-image` to skip
the illustration).

`--guidance "<text>"` adds a free-text instruction that steers the note body **and**
the illustration (tone, target audience, which angle to emphasize). It is recorded
in the note's frontmatter. Guidance does not change idempotency — the same input is
still skipped unless you pass `--overwrite` (so you can re-run with new guidance).

`--pages {N|auto}` turns the single illustration into a **multi-page series** that
teaches one facet per page (overview → mechanism → example → caveats), all in one
consistent visual style (later pages are generated with the first page as a
reference image). It is opt-in: without the flag you get one image as before.
**Each page is a separate image API call, so `--pages N` costs N× the image
generation** (capped at 6 pages); `--no-image` overrides it and generates nothing.
See [ADR 0012](docs/adr/0012-multi-page-illustration.md).

### Revise an existing note

Improve one part of a note without regenerating the whole thing:

```bash
asb-revise "Transformer" "Make the summary simpler"            # rewrite a text section
asb-revise "AWS" "Redraw the illustration on a white background" --illustration
asb-revise "AWS" "Expand the background" --section background   # force a section
```

`asb-revise` finds the note by title or filename, then rewrites **only** the
targeted body section (`summary` / `background` / `key_takeaways`) or redraws the
illustration using the existing image as a style reference (so the look is kept
and only what you asked for changes). Without `--section` / `--illustration` the
target is inferred from the instruction. Edits are written in place — the Vault is
Git-managed, so history lives there. See
[ADR 0014](docs/adr/0014-note-revision.md).

## Features

- **Three knowledge types:** AI **concepts**, **news URLs** (fetched &
  summarized — including JS-rendered sites), and **comparisons** (with a table).
- **Educational illustrations:** a consistent, hand-drawn visual per note
  (gpt-image-2), optionally split into a multi-page series (`--pages`).
- **Structured Markdown notes:** summary, background, key takeaways, related
  notes, references, tags — readable without any AI tool.
- **Natural-language revision:** `asb-revise` improves one section or redraws the
  illustration of an existing note, in place.
- **Automatic linking:** the `asb-relink` Claude Code skill connects notes into a
  graph at no OpenAI cost; backlinks come from Obsidian.
- **Capture from anywhere:** a local `00 Inbox` queue (`asb-inbox`) and chat
  capture via Claude Code Channels (Telegram) — local-first, no fixed hosting
  cost.
- **Instant generation on the go (optional):** an AWS Lambda endpoint runs the
  same pipeline in the cloud and commits the note to a Git-backed vault, so you
  can generate from your phone without your Mac being on — infra ≈ free
  (scale-to-zero). Setup: [DEPLOY_SERVERLESS.md](docs/DEPLOY_SERVERLESS.md),
  design: [ADR 0015](docs/adr/0015-serverless-instant-generation.md).
- **Monthly digest:** `asb-digest` turns [ledge.ai](https://ledge.ai/)'s 30-day
  access ranking into a single note + overview illustration of the month's top
  AI stories.

## How it works

```
URL / Concept / Comparison
        │
        ▼
  Input Classifier ──▶ Extractor (LLM)
        │
        ▼
  Knowledge Object  ← the single source of truth
        │
        ▼
 Educational Planner
        │
        ├──▶ Markdown Generator
        ├──▶ Illustration Generator (gpt-image-2)
        └──▶ Knowledge Linker
        │
        ▼
   Obsidian Vault (external)
```

Everything flows through the Knowledge Object, so new output formats consume the
same canonical representation. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/DATA_MODEL.md](docs/DATA_MODEL.md), and the before/after diagrams in
[docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md).

The Obsidian vault lives **outside** this repository (configured via
`vault_path`); this repo tracks only code and docs, never knowledge data
(see [ADR 0002](docs/adr/0002-vault-and-layout.md)).

## Connecting notes

As your vault grows, connect notes into a knowledge graph:

- **`asb-link`** (deterministic, free): index the vault and safely rewrite a
  note's "Related Notes" section.
- **`asb-relink` Claude Code skill** (smart, no OpenAI cost): reads the whole
  vault, decides which notes relate (and how), and applies the links — using your
  Claude subscription, not the OpenAI API.

## Capture from anywhere

Capture is decoupled from processing by a queue, so everything runs locally with
no fixed hosting cost ([ADR 0006](docs/adr/0006-capture-interface-local-first.md)).

- **Inbox queue:** drop a stub note (a URL or concept) into `00 Inbox/` from
  Obsidian; run `uv run asb-inbox` to turn the queue into notes.
- **Chat capture (Telegram):** message a bot via
  [Claude Code Channels](https://code.claude.com/docs/en/channels); Claude Code
  on your machine runs `asb` and replies. See
  [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md) for the step-by-step setup.
- **Instant, from your phone (optional):** an AWS Lambda endpoint generates in the
  cloud even when your Mac is off — trigger it from an iOS Shortcut. Setup:
  [docs/DEPLOY_SERVERLESS.md](docs/DEPLOY_SERVERLESS.md).

### Login-required sites (captured content)

For pages behind a login (incl. free-membership walls) that `asb` cannot fetch,
**bring the body text yourself** from your own logged-in browser — via an Inbox
stub, `asb --captured-from <URL>`, or Claude Code reading the page through the
Claude in Chrome extension. ASB never handles your credentials or cookies; it
just summarizes the text you give it, stored as News under the source URL
([ADR 0009](docs/adr/0009-captured-content-ingestion.md)). See
[docs/CAPTURED_CONTENT.md](docs/CAPTURED_CONTENT.md) for the step-by-step guide.

## Monthly digest

`asb-digest` builds a one-page overview of the month's most-read AI news. It reads
[ledge.ai](https://ledge.ai/)'s **30-day access ranking**, writes a one-line
summary per story, and generates a digest note + an overview illustration under
`08 Digests` ([ADR 0010](docs/adr/0010-monthly-news-digest.md)).

```bash
uv run asb-digest                       # this month, top 10 (fully automatic)
uv run asb-digest --month 2026-08 --top 5
```

**Higher-quality (Claude Code):** the `asb-digest` skill reads the actual article
bodies and writes the labels/summaries itself — better captions, and **no OpenAI
text cost** (only the illustration is billed;
[ADR 0011](docs/adr/0011-digest-claude-authored-labels.md)).

## Philosophy

This project is **not** an image generator and **not** a note-taking app — it is
a **knowledge operating system**. Images, Markdown, and Git are outputs; the
product is organized knowledge. The guiding principles:

- **Knowledge over content** — create reusable knowledge, not posts.
- **Consistency over creativity** — the same concept is always explained and
  drawn the same way.
- **Automation with human control** — the system automates the repetitive work;
  humans own knowledge quality.
- **Long-term maintainability** — every decision should still make sense years
  from now.

The full vision and long-term goals live in
[docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md).

## Documentation

Design docs are in Japanese; the README is bilingual.

| Document | Purpose |
|----------|---------|
| [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md) | Vision and long-term goals |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md) | Before/after architecture diagrams |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | The Knowledge Object schema |
| [docs/DEPLOY_SERVERLESS.md](docs/DEPLOY_SERVERLESS.md) | Deploy the serverless instant-generation endpoint |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Development roadmap |
| [docs/CAPTURED_CONTENT.md](docs/CAPTURED_CONTENT.md) | Capturing login-required articles |
| [docs/adr/](docs/adr/) | Architecture Decision Records |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Setup & runtime troubleshooting |
| [CLAUDE.md](CLAUDE.md) | Engineering guide for AI-assisted development |

## Roadmap & status

🚧 Active development. **Phases 1–4 complete** (foundation, educational content,
knowledge organization, local-first capture). Recent additions: **multi-page
illustrations** (`--pages`), **natural-language note revision** (`asb-revise`),
and **optional serverless instant generation** (generate from your phone).
**Phase 5 — AI Research Assistant** is next. See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

Contributions are welcome — this project prefers small, reviewable, issue-driven
changes. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2026 ttk1010
