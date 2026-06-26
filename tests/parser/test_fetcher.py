"""Tests for article parsing (Issue #15). Network fetching is not exercised."""

import pytest

from backend.parser.fetcher import MAX_ARTICLE_CHARS, FetchError, parse_article

HTML = """
<html>
  <head><title>OpenAI ships GPT</title></head>
  <body>
    <nav>menu noise</nav>
    <script>var x = 1;</script>
    <p>OpenAI announced a new model today.</p>
    <p>It improves reasoning.</p>
    <footer>copyright</footer>
  </body>
</html>
"""


def test_parse_extracts_title_and_paragraphs() -> None:
    article = parse_article(HTML, "https://example.com/news")

    assert article.title == "OpenAI ships GPT"
    assert "OpenAI announced a new model today." in article.text
    assert "It improves reasoning." in article.text
    # Noise elements are stripped.
    assert "menu noise" not in article.text
    assert "var x" not in article.text
    assert "copyright" not in article.text
    assert article.url == "https://example.com/news"


def test_parse_falls_back_to_full_text_without_paragraphs() -> None:
    article = parse_article("<html><body><div>Just a div</div></body></html>", "u")
    assert "Just a div" in article.text


def test_parse_rejects_empty_document() -> None:
    with pytest.raises(FetchError, match="No readable text"):
        parse_article("<html><body></body></html>", "https://example.com")


def test_parse_caps_text_length() -> None:
    big = "<p>" + ("word " * 10_000) + "</p>"
    article = parse_article(f"<html><body>{big}</body></html>", "u")
    assert len(article.text) <= MAX_ARTICLE_CHARS
