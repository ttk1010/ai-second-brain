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


def test_parse_prefers_jsonld_article_body() -> None:
    html = """
    <html><head><title>News</title>
    <script type="application/ld+json">
    {"@type": "NewsArticle", "headline": "X", "articleBody": "The real body from JSON-LD."}
    </script></head>
    <body><p>nav noise</p></body></html>
    """
    article = parse_article(html, "https://example.com/a")
    assert article.text == "The real body from JSON-LD."


def test_parse_jsonld_handles_graph_list() -> None:
    html = """
    <html><head><title>News</title>
    <script type="application/ld+json">
    [{"@type": "WebPage"}, {"@type": "Article", "articleBody": "Body in a list."}]
    </script></head><body></body></html>
    """
    article = parse_article(html, "u")
    assert article.text == "Body in a list."


def test_parse_extracts_nuxt_content_for_spa() -> None:
    # Simulates a Nuxt SPA (e.g. ledge.ai): body lives in window.__NUXT__,
    # static <p> tags are only navigation noise.
    nuxt = (
        r'window.__NUXT__=(function(a){return {content:"'
        r":::small\n画像\n:::\n\n"  # ::: directive + escaped Japanese
        r"Anthropicは7つの方法を"
        r"[公式ブログ](https://claude.com){target=\"_blank\"}"
        r'で公開した。"}}(0))'
    )
    html = (
        "<html><head><title>Article</title></head>"
        f"<body><p>related</p><script>{nuxt}</script></body></html>"
    )
    article = parse_article(html, "https://ledge.ai/articles/x")

    assert "7つの方法" in article.text  # 7つの方法
    assert "公式ブログ" in article.text  # link text kept (公式ブログ)
    # Directives, attribute blocks, and link URLs are stripped.
    assert ":::" not in article.text
    assert "target=" not in article.text
    assert "claude.com" not in article.text
    # Did not fall back to the navigation paragraph.
    assert "related" not in article.text


def test_paragraphs_used_when_no_structured_data() -> None:
    article = parse_article(HTML, "u")
    assert "OpenAI announced a new model today." in article.text
