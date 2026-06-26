"""Fetch and extract readable article text from a URL.

The fetcher is an abstraction (like ``LLMProvider``) so the News Extractor and
its tests never depend on the network or a specific HTTP/HTML library. The HTML
parsing is separated from the network call so it can be unit-tested offline.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

# A few KB of article text is plenty for the LLM; cap it to control token cost.
MAX_ARTICLE_CHARS = 12_000


class FetchError(Exception):
    """Raised when an article cannot be fetched or parsed."""


@dataclass(frozen=True)
class FetchedArticle:
    """The readable content extracted from a web page."""

    url: str
    title: str
    text: str


class ArticleFetcher(ABC):
    """Abstract article fetcher."""

    @abstractmethod
    def fetch(self, url: str) -> FetchedArticle:
        """Fetch ``url`` and return its readable title and body text.

        Raises:
            FetchError: If the page cannot be retrieved or has no usable text.
        """


class HttpArticleFetcher(ArticleFetcher):
    """Fetches articles over HTTP and extracts text with BeautifulSoup.

    ``httpx`` and ``bs4`` are imported lazily so importing this module never
    requires the packages to be present (mirrors the OpenAI providers).
    """

    def __init__(self, *, timeout: float = 15.0, user_agent: str = "AI-Second-Brain/0.1") -> None:
        self._timeout = timeout
        self._user_agent = user_agent

    def fetch(self, url: str) -> FetchedArticle:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - defensive
            raise FetchError("The 'httpx' package is required for HttpArticleFetcher.") from exc

        try:
            response = httpx.get(
                url,
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": self._user_agent},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FetchError(f"Failed to fetch {url}: {exc}") from exc

        return parse_article(response.text, url)


def parse_article(html: str, url: str) -> FetchedArticle:
    """Extract the title and main text from an HTML document.

    Tries structured sources first so JS-rendered pages still work, falling back
    to static paragraphs:
      1. JSON-LD ``NewsArticle.articleBody`` (standard, many news sites)
      2. Nuxt ``window.__NUXT__`` ``content`` field (e.g. ledge.ai)
      3. static ``<p>`` extraction

    Raises:
        FetchError: If no readable text can be extracted.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - defensive
        raise FetchError("The 'beautifulsoup4' package is required to parse articles.") from exc

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""

    text = _extract_jsonld_body(soup) or _extract_nuxt_content(html) or _extract_paragraphs(soup)
    if not text:
        raise FetchError(f"No readable text found at {url}.")

    return FetchedArticle(url=url, title=title, text=text[:MAX_ARTICLE_CHARS])


def _extract_paragraphs(soup: object) -> str:
    """Extract visible paragraph text from static HTML (the original strategy)."""
    # Drop non-content elements before reading text.
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside"]):
        tag.decompose()

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paragraphs if p)
    if not text:
        # Fall back to the whole document text when there are no <p> tags.
        text = soup.get_text("\n", strip=True)
    return text.strip()


def _extract_jsonld_body(soup: object) -> str | None:
    """Extract ``articleBody`` from a schema.org Article JSON-LD block, if any."""
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        body = _find_article_body(data)
        if body:
            return body.strip()
    return None


def _find_article_body(data: object) -> str | None:
    """Recursively search a parsed JSON-LD structure for an articleBody."""
    if isinstance(data, dict):
        body = data.get("articleBody")
        if isinstance(body, str) and body.strip():
            return body
        for value in data.values():
            found = _find_article_body(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_article_body(item)
            if found:
                return found
    return None


# Matches the article body stored as a JS string literal in the Nuxt payload.
_NUXT_CONTENT_RE = re.compile(r'content:"((?:[^"\\]|\\.)*)"')


def _extract_nuxt_content(html: str) -> str | None:
    """Extract the article body from a Nuxt ``window.__NUXT__`` payload, if any.

    Nuxt SPAs (e.g. ledge.ai) embed the article body as a ``content`` field
    holding Markdown. The longest such field is the main article; related-article
    entries only carry short excerpts.
    """
    if "__NUXT__" not in html:
        return None
    candidates = _NUXT_CONTENT_RE.findall(html)
    if not candidates:
        return None
    longest = max(candidates, key=len)
    cleaned = _clean_nuxt_markdown(_js_unescape(longest))
    return cleaned or None


def _js_unescape(s: str) -> str:
    """Decode the escapes used in Nuxt JS string literals (e.g. ``\\u002F``)."""
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    s = s.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "")
    s = s.replace('\\"', '"').replace("\\'", "'")
    return s.replace("\\\\", "\\")


def _clean_nuxt_markdown(s: str) -> str:
    """Reduce Markdown-with-directives to readable text for the LLM."""
    s = re.sub(r"\{[^}]*\}", "", s)  # drop attribute blocks like {target="_blank"}
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)  # links -> link text
    s = re.sub(r"^:::.*$", "", s, flags=re.MULTILINE)  # drop ::: directive markers
    s = re.sub(r"\n{3,}", "\n\n", s)  # collapse blank runs
    return s.strip()
