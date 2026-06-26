# System Architecture

Version: 1.0

Status: Draft

---

# Purpose

This document defines the high-level architecture of AI Second Brain.

Its purpose is to describe how information flows through the system and how each component is responsible for transforming raw input into reusable knowledge.

Implementation details belong in the source code.

This document focuses on architecture, responsibilities, and data flow.

---

# Design Principles

The architecture should satisfy the following principles:

* Simple over clever
* Modular over monolithic
* Knowledge-first
* Human-readable outputs
* AI-assisted, not AI-dependent
* Easy to extend

Each component should have a single responsibility.

---

# High-Level Architecture

```
                        User
                          │
                          ▼
          URL / AI Concept / News
                          │
                          ▼
                 Input Classifier
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
   Concept Extractor               News Extractor
          │                               │
          └───────────────┬───────────────┘
                          ▼
              Knowledge Object Builder
                          │
                          ▼
                  Knowledge Object
                          │
                          ▼
               Educational Planner
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
Markdown Generator  Illustration Generator  Metadata Generator
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                 Knowledge Linker
                          │
                          ▼
                  Knowledge Node
                          │
                          ▼
                  Obsidian Vault
                          │
                          ▼
                    Git Repository
                          │
                          ▼
                        GitHub
```

---

# Core Components

## 1. Input Layer

### Responsibility

Receive user input.

Supported inputs:

* AI concepts
* URLs
* Research papers
* News articles

The input layer should remain extremely lightweight.

Its only job is accepting input.

---

## 2. Input Classifier

### Responsibility

Determine the input type.

Possible classification labels include:

* Concept
* News
* Research Paper
* Documentation
* Unknown

In Phase 1, these labels map onto only two processing pipelines (see ADR 0001):

* Concept → Concept pipeline
* News → News pipeline
* Research Paper / Documentation → handled provisionally by the News pipeline (treated as URL input)
* Unknown → falls back to the News pipeline if it parses as a URL; otherwise the system fails fast with an explicit error

Dedicated pipelines for Research Paper and Documentation are deferred to a future issue.

---

## 3. Knowledge Pipelines

Different input types require different processing.

Examples:

### Concept Pipeline

Input:

Transformer

Output:

* concept explanation
* related concepts
* educational structure

---

### News Pipeline

Input:

https://ledge.ai/...

Output:

* summary
* technology
* companies
* impact
* related concepts

Both pipelines eventually produce the same normalized structure.

---

# Knowledge Object Builder

This component converts every input into the canonical internal representation:
the **Knowledge Object**. It is the single component responsible for normalization.

The authoritative schema is defined in `DATA_MODEL.md`. A Knowledge Object is
structured along these fields:

```text
KnowledgeObject
├── id
├── source
├── title
├── summary
├── concepts
├── entities
├── relationships
├── educational_plan
├── references
├── metadata
└── outputs (optional)
```

Downstream components should never care whether the original input was a keyword or a URL.

> Note: an earlier draft called this component "Knowledge Normalizer". The name
> has been unified to **Knowledge Object Builder** (ADR 0001). For data-structure
> details, `DATA_MODEL.md` is the source of truth.

---

# Educational Planner

This is the heart of the system.

Its responsibility is not summarization.

Its responsibility is education.

It decides:

* What should be explained?
* What should be visualized?
* Which concepts require emphasis?
* What prior knowledge should be assumed?

Outputs from this component drive both illustration generation and Markdown generation.

---

# Illustration Generator

Purpose:

Transform educational plans into consistent visual explanations.

The illustration generator should always follow the project's illustration policy.

Responsibilities include:

* selecting the layout
* selecting the aspect ratio
* determining visual hierarchy
* maintaining visual consistency

Illustration styles should never be embedded directly in application code.

They belong in dedicated prompt templates.

---

# Markdown Generator

Generate human-readable notes.

Each note follows the standard template:

* Frontmatter
* Summary
* Illustration
* Background
* Key Takeaways
* Related Notes
* References
* Tags

Markdown is the primary long-term knowledge format.

---

# Knowledge Linker

The linker enriches generated notes by identifying relationships.

Examples:

* related concepts
* prerequisite knowledge
* follow-up topics
* existing notes

This component transforms isolated notes into a connected knowledge graph.

---

# Storage Layer

## Obsidian Vault

The Vault is the primary knowledge repository.

It lives **outside this code repository**, in an external location configured via
`vault_path` (see ADR 0002). The Storage Layer writes Knowledge Nodes into that
external Vault; this code repository never contains the knowledge data itself.

All generated knowledge should remain editable without AI.

Folder organization is defined separately.

---

## Git

Git here refers to the **external Vault's own optional version control** — distinct
from this code repository's Git. When the external Vault is under Git and
`auto_commit` is enabled, generated changes are committed there.

Git provides:

* version history
* reproducibility
* rollback
* synchronization

Every meaningful change should be committed.

---

## GitHub

GitHub serves as:

* backup
* collaboration platform
* project management
* issue tracking

---

# Data Flow

Every execution follows the same lifecycle.

```
Input

↓

Classification

↓

Knowledge Extraction

↓

Normalization

↓

Educational Planning

↓

Illustration

↓

Markdown

↓

Knowledge Linking

↓

Vault

↓

Git

↓

GitHub
```

---

# Repository Layout

```
backend/
    parser/
    planner/
    prompts/
    image/
    markdown/
    linker/
    storage/
    services/
    models/

docs/

tests/

scripts/
```

The Obsidian Vault is **not** part of this layout. It is external and referenced
via `vault_path` (see ADR 0002).

Each directory should have a clear and independent responsibility.

---

# AI Responsibilities

ChatGPT

* architecture
* educational design
* illustration prompt design

Claude Code

* implementation
* testing
* refactoring
* repository maintenance

Other AI assistants

* benchmarking
* experimentation
* research

---

# Extensibility

Future components may include:

* RSS ingestion
* arXiv integration
* YouTube ingestion
* Podcast summarization
* Semantic search
* Local embedding generation
* Knowledge recommendation
* Timeline visualization

These should integrate by extending existing pipelines rather than replacing them.

---

# Architectural Constraints

The architecture should avoid:

* tightly coupled components
* duplicated business logic
* AI-specific assumptions in core modules
* hardcoded prompt text
* implementation-specific storage logic

Components should communicate through well-defined data structures.

---

# Long-Term Architecture Vision

AI Second Brain is designed as a knowledge operating system.

The architecture should evolve toward a modular platform where new knowledge sources, AI models, and output formats can be added without redesigning the system.

The ultimate objective is a system where knowledge continuously grows, connects, and becomes easier to understand over time.
