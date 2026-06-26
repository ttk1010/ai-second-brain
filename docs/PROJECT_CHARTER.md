# Project Charter

Version: 1.0

Status: Active

---

# Mission

Build a personal AI-powered Second Brain that transforms AI-related information into structured, visual, and reusable knowledge.

The system should enable continuous learning by turning articles, research papers, technical concepts, and news into a long-term knowledge base that evolves together with its owner.

---

# Core Design Principle

Every input should first become a structured Knowledge Object.

Knowledge Objects represent the canonical understanding of a topic.

All outputs—including illustrations, Markdown, metadata, and future export formats—must be generated from the same Knowledge Object.

This ensures consistency, extensibility, and long-term maintainability.

---

# Vision

Artificial Intelligence is evolving faster than any individual can keep up with.

Instead of repeatedly searching for the same information, AI Second Brain aims to create an environment where knowledge is continuously accumulated, connected, and refined.

The long-term vision is to make learning AI feel less like collecting notes and more like growing an intelligent research companion.

---

# Guiding Principles

## Knowledge over Content

The purpose of the project is not to generate content.

The purpose is to generate reusable knowledge.

Every output should provide long-term value.

---

## Understanding over Summarization

Simply summarizing an article is not enough.

The system should explain:

* What happened?
* Why does it matter?
* How does it relate to existing knowledge?
* What should be learned next?

---

## Visual Learning

Educational illustrations are a core feature.

Images should improve understanding, not decoration.

Every illustration should maintain a consistent visual language across the entire knowledge base.

---

## Human-in-the-Loop

AI accelerates knowledge creation.

Humans validate knowledge quality.

The project values automation without sacrificing accuracy.

---

## Long-term Maintainability

The project should remain understandable years from now.

Every architectural decision should prioritize simplicity, extensibility, and readability.

---

# Goals

The system should be able to:

* Accept a URL or AI-related keyword as input.
* Automatically determine whether the input is a concept or a news article.
* Analyze the input and extract meaningful knowledge.
* Generate a consistent educational illustration.
* Produce structured Markdown notes.
* Link related concepts automatically.
* Store the knowledge inside an Obsidian Vault.
* Track every change using Git and GitHub.

---

# Non-Goals

The following are intentionally excluded from the first version:

* Multi-user support
* SaaS deployment
* Public web interface
* Authentication
* Vector databases
* Retrieval-Augmented Generation (RAG)
* Autonomous agents making irreversible changes
* Complex workflow orchestration

These may be revisited in future phases.

---

# Product Scope

## Inputs

The system accepts two primary input types:

### AI Concepts

Examples:

* Transformer
* MCP
* RLHF
* LoRA
* Agentic Commerce

### AI-related URLs

Examples:

* AI news
* Research papers
* Official announcements
* Blog posts
* Technical documentation

---

# Outputs

Each execution produces:

* Educational summary
* Educational illustration
* Structured Markdown
* Metadata
* Related note suggestions
* Git history

Knowledge should always remain editable by humans.

---

# Educational Illustration Principles

Illustrations exist to teach.

Every image should be:

* technically accurate
* visually approachable
* information-rich
* easy to understand
* consistent with previous illustrations

Preferred style:

* hand-drawn
* soft lines
* pastel colors
* white background
* slide-friendly
* textbook-inspired

The system automatically selects the most appropriate aspect ratio based on the information structure.

| Information Type       | Aspect Ratio |
| ---------------------- | ------------ |
| Process / Workflow     | 16:9         |
| Hierarchical Structure | 4:3          |
| Single Concept         | 1:1          |
| Step-by-step Guide     | 9:16         |

---

# Knowledge Organization

Knowledge is organized independently of implementation details.

Recommended structure:

```
00 Inbox/
01 Concepts/
02 Models/
03 Companies/
04 Development/
05 Laws/
06 News/
07 Papers/
08 Images/
Templates/
```

Markdown files should remain readable without AI tools.

---

# Technology Principles

The implementation should favor:

* Python
* FastAPI
* uv
* Obsidian
* Git
* GitHub

Technology choices may evolve without changing the project's philosophy.

---

# AI Responsibilities

Different AI systems have different roles.

## ChatGPT

* Product design
* Architecture
* Educational design
* Illustration prompt engineering
* Design reviews

## Claude Code

* Implementation
* Refactoring
* Testing
* Repository maintenance

## Other AI Assistants

May be used for:

* Research
* Benchmarking
* Alternative implementations

No single AI should become a project dependency.

---

# Development Philosophy

Development follows an issue-driven workflow.

Every feature should begin as a GitHub Issue.

Each Issue should define:

* Why
* Goal
* Tasks
* Definition of Done

Small, reviewable iterations are preferred over large implementations.

---

# Roadmap

## Phase 1 — Foundation

* Repository setup
* Markdown generation
* Obsidian integration
* URL and keyword processing

## Phase 2 — Educational Content

* Illustration generation
* News analysis
* Concept analysis

## Phase 3 — Knowledge Graph

* Automatic linking
* Related notes
* Metadata enrichment

## Phase 4 — Automation

* CLI
* FastAPI
* Browser extension
* Mobile sharing

## Phase 5 — AI Research Assistant

* Knowledge recommendations
* Related news detection
* Learning suggestions
* Continuous knowledge evolution

---

# Success Criteria

The project is successful when:

* AI learning becomes frictionless.
* Knowledge accumulates with minimal manual effort.
* Every new article strengthens the existing knowledge base.
* The Obsidian graph naturally reflects conceptual relationships.
* Future AI assistants can understand and build upon the stored knowledge.

---

# Long-Term Vision

AI Second Brain is not intended to be another note-taking application.

It is intended to become a personal AI research environment where knowledge continuously evolves.

The ultimate goal is to create a system in which both humans and AI collaborate to understand, organize, and expand knowledge over time.

Rather than asking:

> "What did this article say?"

the user should naturally begin asking:

> "How does this change what I already know?"
