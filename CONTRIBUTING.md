# Contributing to AI Second Brain

Thanks for your interest in contributing! This project values small, reviewable
changes and clear knowledge over feature count.

## Development setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
uv sync --dev          # install dependencies into a virtual environment
uv run ruff format .   # format
uv run ruff check .    # lint
uv run pytest          # run tests
```

CI runs the same lint, format check, and tests on every push and pull request.

## Workflow

This is an issue-driven project:

1. Start from (or open) a GitHub Issue describing the why, goal, tasks, and
   definition of done.
2. Branch from `main`: `feature/<name>`, `fix/<name>`, `refactor/<component>`,
   or `docs/<topic>`.
3. Keep changes small and focused — prefer several small PRs over one large one.
4. Add tests for non-trivial behavior. Tests should not require network or API
   keys (use the provider abstractions / mocks).
5. Update docs alongside code (README for user-facing changes, `docs/` for
   architectural ones, docstrings, and `docs/adr/` for significant decisions).
6. Open a pull request; make sure CI is green.

## Guidelines

- Follow the engineering principles in [CLAUDE.md](CLAUDE.md) and the
  architecture in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Every feature revolves around the **Knowledge Object** — outputs are generated
  from it, never directly from raw input.
- Use modern Python (type hints, dataclasses/pydantic, dependency injection);
  avoid global state and duplicated logic.
- Commit messages should describe intent, not just "fix" or "update".

## Reporting issues

Open a GitHub Issue with steps to reproduce, expected vs actual behavior, and
your environment. For setup snags, check
[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) first.
