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
vault/
```

The repository intentionally keeps a simple structure.

Knowledge lives inside the Vault.

Implementation lives inside the backend.

Documentation lives inside docs.

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

🚧 Early Development

The architecture has been designed.

Implementation is beginning with the foundation of the knowledge pipeline.
