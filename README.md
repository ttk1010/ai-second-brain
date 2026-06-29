# AI Second Brain

> Capture. Understand. Visualize. Remember.

AI Second Brain is a personal knowledge system that transforms AI news, research papers, and technical concepts into a structured, visual, and continuously evolving knowledge base.

Instead of simply reading AI content, the goal is to build a **Second Brain** that grows over time—helping both humans and AI understand, connect, and reuse knowledge.

---

# Vision

Artificial Intelligence evolves every day.

New models, new frameworks, new research papers, new APIs, and new regulations appear faster than anyone can remember.

Reading is no longer enough.

The purpose of AI Second Brain is to convert fragmented information into long-term knowledge assets.

Every article, concept, and paper should become something that can be understood today and rediscovered years later.

---

# Core Philosophy

This project is **not** an image generation tool.

It is **not** a note-taking application.

It is a **knowledge operating system**.

Images are outputs.

Markdown is an output.

Git is an output.

The real product is **organized knowledge**.

---

# What Happens

Given only a URL or an AI-related keyword, the system automatically:

```
URL / Keyword
        │
        ▼
Knowledge Extraction
        │
        ▼
Knowledge Object
        │
        ▼
Educational Planning
        │
        ▼
┌──────────────────────────┐
│    Output Generation     │
├──────────────────────────┤
│ • Markdown               │
│ • Illustration           │
│ • Metadata               │
│ • Related Notes          │
└──────────────────────────┘
        │
        ▼
Knowledge Node
        │
        ▼
Obsidian Vault
        │
        ▼
Git
        │
        ▼
GitHub
```

The Knowledge Object is the canonical representation of knowledge within the system. All generated outputs originate from this single source of truth before being stored as interconnected Knowledge Nodes in the Second Brain.

The Obsidian Vault lives outside this repository (configured via `vault_path`). The trailing `Git → GitHub` step refers to the **external Vault's own optional version control** — committed when `auto_commit` is enabled and the Vault is under Git — and is distinct from this code repository's Git (see ADR 0002).

The long-term goal is to make knowledge accumulation almost effortless.

---

# Example Inputs

```
Transformer
```

```
MCP
```

```
https://ledge.ai/...
```

```
https://openai.com/news/...
```

---

# Example Outputs

For every input, the system generates:

- Educational illustration
- Structured Markdown note
- Metadata
- Related knowledge links
- Obsidian note
- Git history

Every output should be reusable.

---

# Design Principles

The project follows a few simple principles.

## Knowledge over Content

Do not create content.

Create reusable knowledge.

---

## Consistency over Creativity

Educational materials should look and feel consistent.

The same concept should always be explained using the same visual language.

---

## Automation with Human Control

The system automates repetitive work.

Humans remain responsible for reviewing knowledge quality.

---

## Long-term Maintainability

Every design decision should still make sense years later.

Avoid unnecessary complexity.

---

# Current Scope

The first milestone focuses on building a Minimum Viable Pipeline.

- Accept URL or keyword input
- Understand AI concepts or news
- Generate educational illustrations
- Generate Markdown
- Save to an Obsidian Vault
- Track changes with Git

Future versions will introduce:

- Knowledge graph generation
- Automatic related-note discovery
- AI-assisted knowledge recommendations
- Mobile capture workflows
- Browser extensions
- Daily AI digest generation

---

# Repository Structure

```
backend/
docs/
scripts/
tests/
```

The repository intentionally keeps a simple structure.

Implementation lives inside the backend.

Documentation lives inside docs.

Knowledge lives inside an **external** Obsidian Vault, located outside this
repository and configured via `vault_path`. This repository tracks only code
and documentation — never the knowledge data itself (see ADR 0002).

---

# Documentation

Project documentation is intentionally separated.

| Document | Purpose |
|----------|---------|
| README.md | Project overview |
| docs/PROJECT_CHARTER.md | Vision and long-term goals |
| CLAUDE.md | Development guide for AI coding agents |
| docs/ARCHITECTURE.md | System architecture *(planned)* |
| docs/ROADMAP.md | Development roadmap *(planned)* |

---

# Development Setup

This project uses [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
# Install dependencies (creates a virtual environment)
uv sync --dev

# Lint and format
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest
```

Continuous integration runs the same lint, format check, and tests on every
push and pull request.

---

# Usage

1. Copy the example settings and point `vault_path` at your external Obsidian
   Vault:

   ```bash
   cp config/settings.example.toml config/settings.toml
   # then edit vault_path (and optionally llm_model, default_language)
   ```

2. Provide your OpenAI API key. Create a `.env` file in the repository root
   (it is git-ignored):

   ```bash
   echo 'OPENAI_API_KEY=sk-...' > .env
   ```

3. Generate a note from an AI concept:

   ```bash
   uv run asb "Transformer"
   ```

   The structured Markdown note is written into your Vault (e.g.
   `01 Concepts/Transformer.md`), together with an educational illustration
   saved under `Images/` (e.g. `Images/Transformer.png`) and embedded in the
   note. Use `--overwrite` to replace an existing note.

   You can also pass an article URL to capture AI news:

   ```bash
   uv run asb "https://openai.com/news/..."
   ```

   The article is fetched, summarized, illustrated, and saved under `06 News/`.

   Or compare several things in one note with `--compare`:

   ```bash
   uv run asb --compare "GPT, Claude, Gemini"
   ```

   This produces a structured comparison note (with a comparison table) under
   `04 Comparisons/`, linked to each item's own note.

> AI **concepts**, **news URLs**, and **comparisons** are processed end to end
> (summary, Educational Plan, and illustration).

## Connecting notes

As your Vault grows, connect the notes into a knowledge graph. Two layers:

- **`asb-link`** (deterministic, free): indexes the Vault and safely rewrites a
  note's "Related Notes" section.

  ```bash
  uv run asb-link index                       # list all notes as JSON
  uv run asb-link apply "<vault>/01 Concepts/Transformer.md" \
    --link "Neural Network:prerequisite" --link "Attention:related"
  ```

  `apply` only touches the Related Notes section and is idempotent. Reverse
  links appear automatically via Obsidian's native backlinks.

- **`asb-relink` Claude Code skill** (smart, no OpenAI cost): in Claude Code, run
  the `asb-relink` skill to read the whole Vault, decide which notes are related
  (including spelling variants and conceptual closeness), and apply the links for
  you. It uses your Claude subscription only — it makes **no OpenAI API calls**.

## Capture from anywhere

Capture is decoupled from processing by a queue, so everything runs locally with
no fixed hosting cost (see ADR 0006). Re-running is safe — an existing
concept/URL is skipped, not regenerated.

### Inbox queue

Drop a stub note containing a URL or concept into your Vault's `00 Inbox/` (e.g.
from Obsidian on your phone). When your machine is on, process the queue:

```bash
uv run asb-inbox            # turns each 00 Inbox stub into a note, then clears it
```

Run it manually, or schedule it (cron / launchd). `--no-image` and `--overwrite`
are supported.

### Chat capture via Claude Code Channels

Capture from your phone by messaging a Telegram bot, using
[Claude Code Channels](https://code.claude.com/docs/en/channels). A message is
routed to Claude Code running on your machine, which runs `asb` and replies. No
server to host; it uses your Claude subscription (OpenAI cost is only the usual
per-note generation).

Setup:

1. Enable Claude Code Channels and connect a Telegram bot (per the Channels
   docs). A terminal/session must stay running on your machine.
2. **Pre-approve the actions so it runs unattended.** Channels cannot approve
   permission prompts remotely, so register the capture command and the Telegram
   reply tools in your Claude Code permissions ahead of time. Add them to the
   `permissions.allow` list in your personal `.claude/settings.local.json`
   (gitignored — keep Telegram-related rules here, not in shared settings), then
   restart Claude Code. The exact tool identifiers (e.g. the
   `mcp__…telegram…__reply` reply tool) and a ready-to-merge list are in
   [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
3. Message the bot an AI concept or an article URL. The bundled `asb-capture`
   skill runs `asb` on it and reports the result.

Hitting setup snags? See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

# Development Workflow

This project follows an issue-driven development process.

Every feature starts as a GitHub Issue.

Each Issue should include:

- Why
- Goal
- Tasks
- Definition of Done

Small, reviewable changes are preferred over large implementations.

---

# Long-term Vision

The final objective is not simply to collect notes.

It is to create a personal AI research environment where knowledge continuously evolves.

In the future, AI Second Brain should be able to:

- understand new AI news,
- connect it with existing knowledge,
- identify missing concepts,
- recommend what to learn next,
- and continuously improve the user's understanding of AI.

Ultimately, the system becomes a personal AI research assistant that grows together with its owner.

---

## Project Status

🚧 Active Development

- **Phase 1 — Foundation:** ✅ complete. Concept input → Knowledge Object →
  structured Markdown note saved to the external Vault.
- **Phase 2 — Educational Content:** ✅ complete. Both concepts and news URLs are
  processed end to end, with an Educational Plan, a generated illustration
  (gpt-image-2), and full notes (summary, background, key takeaways).
- **Phase 3 — Knowledge Organization:** ✅ complete. A deterministic vault index
  and safe Related-Notes updater, plus the `asb-relink` Claude Code skill that
  connects notes with no OpenAI cost. Backlinks via Obsidian.
- **Phase 4 — Automation:** ✅ complete. Local-first capture with no fixed cost:
  the `00 Inbox` queue worker (`asb-inbox`) and Claude Code Channels (Telegram)
  chat capture. Idempotent generation and a `--no-image` cost switch.
- **Phase 5 — AI Research Assistant:** ⏭️ next. Recommendations, similar/duplicate
  detection, knowledge-gap detection, and a daily digest.
