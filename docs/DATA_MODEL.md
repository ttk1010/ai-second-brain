# Data Model

Version: 1.0

Status: Draft

---

# Purpose

This document defines the canonical data model used throughout AI Second Brain.

The goal is to establish a single source of truth for representing knowledge within the system.

Every component should consume or produce well-defined data structures rather than exchanging raw text.

---

# Design Philosophy

AI Second Brain distinguishes between two fundamental concepts:

* **Knowledge Object** — the internal, structured representation of knowledge.
* **Knowledge Node** — the persistent knowledge artifact stored in the knowledge base (e.g., an Obsidian note).

This separation ensures that business logic, presentation, and storage remain independent.

---

# Knowledge Lifecycle

```text
Raw Input
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
    ├── Markdown
    ├── Illustration
    ├── Metadata
    └── Related Notes
    │
    ▼
Knowledge Node
    │
    ▼
Obsidian Vault
```

---

# Knowledge Object

The Knowledge Object is the canonical representation of knowledge inside the application.

Every downstream component—including illustration generation, Markdown generation, metadata generation, and knowledge linking—must consume the same Knowledge Object.

The Knowledge Object should never contain presentation-specific information.

---

## Conceptual Structure

```text
KnowledgeObject
├── id
├── source
├── title
├── short_title
├── summary
├── background
├── key_takeaways
├── concepts
├── entities
├── relationships
├── educational_plan
├── references
├── metadata
└── outputs (optional)
```

`short_title` is a concise label used for the note's filename (and illustration
filename); the full descriptive `title` stays in the frontmatter and heading. It
falls back to `title` when empty. For concepts it is just the concept name (e.g.
`Neural Network`); for news it is the key entity and core topic (e.g.
`Midjourney、医療ハードウェアに参入`).

`background` (context and why the topic matters) and `key_takeaways` (the few
points a reader should remember) are reader-facing knowledge content, extracted
alongside the summary. They are distinct from the Educational Plan's
`key_messages`, which guide *how* to teach and illustrate rather than what the
note presents to the reader.

The `outputs` field holds **references only** — file paths or IDs pointing to
generated artifacts (Markdown, illustration, etc.). It never stores the artifact
bodies themselves. This keeps the Knowledge Object free of presentation data
(see ADR 0001).

---

## Responsibilities

A Knowledge Object should represent:

* What the topic is
* Why it matters
* How it works
* How it relates to existing knowledge

It should be independent of:

* Markdown formatting
* Illustration layout
* Obsidian structure
* File names

---

# Educational Plan

The Educational Plan is part of the Knowledge Object.

Its responsibility is to define *how* the knowledge should be taught.

Typical fields may include:

* learning objective
* target audience
* prerequisite knowledge
* key messages
* visualization strategy (including the chosen aspect ratio)

The Educational Plan drives all educational outputs.

The **aspect ratio** of an illustration is decided here, as part of the
`visualization_strategy`. The Educational Planner chooses it (using the
information-type → aspect-ratio mapping in PROJECT_CHARTER.md); the Illustration
Generator only consumes it. Education decides *what* to show; the generator
decides only *how* to render it (see ADR 0001).

---

# Metadata

Metadata describes the knowledge rather than its presentation.

Examples:

* source URL
* publication date
* author
* tags
* categories
* confidence
* reading time
* language

Metadata should be reusable across all output formats.

---

# Relationships

Relationships connect one Knowledge Object to others.

Examples:

* prerequisite
* related concept
* successor
* alternative
* implementation
* regulation
* application

Relationships are logical and independent of storage.

---

# Knowledge Node

A Knowledge Node is the persistent representation of a Knowledge Object.

It is the unit that appears inside the Second Brain.

For the current implementation, a Knowledge Node consists of:

* Markdown note
* Illustration
* Frontmatter
* Metadata
* Backlinks
* References

A Knowledge Node is optimized for human consumption and long-term maintenance.

---

# Knowledge Graph

Knowledge Nodes are connected to form the knowledge graph.

The graph represents conceptual relationships rather than file hierarchy.

Folder structures may aid organization, but the graph is the primary navigation model.

---

# Data Ownership

Each component has a clear responsibility:

| Component                | Owns               |
| ------------------------ | ------------------ |
| Extractors               | Raw input analysis |
| Knowledge Object Builder | Knowledge Object   |
| Educational Planner      | Educational Plan (incl. aspect ratio) |
| Markdown Generator       | Markdown           |
| Illustration Generator   | Illustration       |
| Metadata Generator       | Metadata           |
| Knowledge Linker         | Relationships      |
| Storage Layer            | Knowledge Node     |

No component should modify another component's responsibility directly.

---

# Extensibility

Future output formats should be generated from the same Knowledge Object.

Examples include:

* HTML
* PDF
* PowerPoint
* Web pages
* Flashcards
* Interactive visualizations

No output format should require changes to the core Knowledge Object.

---

# Design Rules

* The Knowledge Object is the single source of truth.
* All generators consume the Knowledge Object.
* Knowledge Nodes are immutable records of generated knowledge until explicitly updated.
* Presentation should never influence the Knowledge Object.
* Storage technology should remain replaceable.

---

# Long-Term Vision

As AI Second Brain evolves, the Knowledge Object becomes the foundation for every capability.

Regardless of future AI models, storage backends, or output formats, all knowledge should flow through the same canonical representation.

By separating **knowledge**, **presentation**, and **storage**, the system remains modular, maintainable, and extensible for years to come.
