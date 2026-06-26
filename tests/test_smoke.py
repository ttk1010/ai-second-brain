"""Smoke test: the backend package and its modules import cleanly.

This guards the project scaffolding (ADR 0002 layout) until real
implementation arrives in later issues.
"""

import importlib

import pytest

BACKEND_MODULES = [
    "backend",
    "backend.parser",
    "backend.planner",
    "backend.prompts",
    "backend.image",
    "backend.markdown",
    "backend.linker",
    "backend.storage",
    "backend.services",
    "backend.models",
]


@pytest.mark.parametrize("module_name", BACKEND_MODULES)
def test_module_imports(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None
