"""Tests for the asb-link CLI (Issue #22)."""

import json
from pathlib import Path

from backend.linker import cli

NOTE = """\
---
title: "BERT"
tags:
  - nlp
---

# BERT

## Related Notes

- [[old]]

## References

- https://x.com
"""


def test_index_prints_json(tmp_path: Path, capsys) -> None:
    (tmp_path / "01 Concepts").mkdir(parents=True)
    (tmp_path / "01 Concepts" / "BERT.md").write_text(NOTE, encoding="utf-8")

    code = cli.main(["index", "--vault", str(tmp_path)])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["title"] == "BERT"
    assert data[0]["tags"] == ["nlp"]


def test_apply_updates_related_section(tmp_path: Path, capsys) -> None:
    note = tmp_path / "BERT.md"
    note.write_text(NOTE, encoding="utf-8")

    code = cli.main(
        ["apply", str(note), "--link", "Transformer:prerequisite", "--link", "Attention"]
    )

    assert code == 0
    content = note.read_text(encoding="utf-8")
    assert "- [[Transformer]] — prerequisite" in content
    assert "- [[Attention]]" in content
    assert "old" not in content
    assert "## References" in content  # untouched


def test_apply_reports_no_change_when_identical(tmp_path: Path, capsys) -> None:
    note = tmp_path / "BERT.md"
    note.write_text(NOTE, encoding="utf-8")
    cli.main(["apply", str(note), "--link", "X"])
    capsys.readouterr()
    cli.main(["apply", str(note), "--link", "X"])
    assert "No change" in capsys.readouterr().out


def test_apply_missing_note_returns_2(tmp_path: Path) -> None:
    assert cli.main(["apply", str(tmp_path / "nope.md"), "--link", "X"]) == 2
