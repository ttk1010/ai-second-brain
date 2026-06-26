# Prompt Style Guide

Version: 1.0

Status: Active

---

# Purpose

This document defines how prompts should be designed throughout AI Second Brain.

Prompts are considered first-class assets.

They should be treated with the same level of care as source code.

Every prompt should be:

* understandable
* reusable
* maintainable
* model-agnostic whenever possible

---

# Core Philosophy

Prompts do not generate knowledge.

Prompts transform a **Knowledge Object** into useful outputs.

The Knowledge Object is always the source of truth.

Never design prompts that rely directly on raw user input if a Knowledge Object is available.

---

# Prompt Architecture

Every prompt should follow the same logical structure.

```text
Role

↓

Goal

↓

Context

↓

Input

↓

Constraints

↓

Output Format
```

This structure improves consistency across different AI models.

---

# Prompt Layers

Prompts should be divided into three layers.

## 1. System Prompt

Defines long-term behavior.

Examples:

* educational tone
* visual consistency
* writing principles

Should rarely change.

---

## 2. Task Prompt

Defines the current task.

Examples:

* Generate an illustration.
* Produce Markdown.
* Extract concepts.

Changes for every feature.

---

## 3. Data Prompt

Contains the actual Knowledge Object.

Should contain structured information only.

Never embed business logic here.

---

# Knowledge Object First

Whenever possible, prompts should consume a Knowledge Object rather than raw text.

Preferred flow:

```text
Raw Input

↓

Knowledge Extraction

↓

Knowledge Object

↓

Prompt

↓

Output
```

This ensures consistency across all generated artifacts.

---

# Prompt Design Principles

## Single Responsibility

One prompt should solve one problem.

Avoid prompts that simultaneously summarize, visualize, classify, and generate metadata.

---

## Explicit Instructions

Prefer explicit instructions over implicit assumptions.

Bad:

"Explain this well."

Good:

"Explain this concept for a software engineer familiar with machine learning."

---

## Structured Outputs

Whenever possible, request structured outputs.

Preferred formats:

* JSON
* Markdown
* YAML

Avoid free-form outputs unless creativity is desired.

---

## Deterministic First

Prioritize consistency over novelty.

The same Knowledge Object should produce similar outputs across multiple runs.

---

# Educational Prompt Principles

Educational prompts should answer:

* What is it?
* Why does it matter?
* How does it work?
* How does it connect to existing knowledge?

Avoid unnecessary jargon.

Prefer conceptual clarity.

---

# Illustration Prompt Principles

Illustrations should teach.

Never decorate.

Illustrations should:

* simplify complexity
* reveal relationships
* explain processes
* emphasize important concepts

Preferred visual style:

* hand-drawn
* soft colors
* white background
* textbook-inspired
* information-rich
* visually calm

---

# Markdown Prompt Principles

Markdown should remain valuable without AI.

Every note should include:

* Summary
* Background
* Illustration
* Key Takeaways
* Related Notes
* References
* Tags

Use concise technical writing.

---

# Prompt Reuse

Avoid duplicating prompts.

Whenever multiple prompts share common behavior:

Extract shared instructions into reusable templates.

---

# Model Independence

Prompts should avoid relying on model-specific behavior whenever possible.

The same prompt should work with:

* ChatGPT
* Claude
* Gemini

Minor adjustments are acceptable.

---

# Prompt Versioning

Every significant prompt should include:

* version
* purpose
* expected input
* expected output

Prompt changes should be reviewed similarly to source code.

---

# Future Prompt Library

The repository will eventually include:

```text
backend/prompts/

├── extraction/
├── education/
├── illustration/
├── markdown/
├── metadata/
├── linking/
└── shared/
```

Each prompt should have a single responsibility.

---

# Long-Term Vision

Prompt engineering is a core capability of AI Second Brain.

The goal is to build a reusable prompt ecosystem where every AI task is modular, testable, and maintainable.

Prompts should evolve together with the architecture rather than being embedded inside application code.
