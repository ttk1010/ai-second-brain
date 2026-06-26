"""Fetch and extract readable article text from a URL.

The fetcher is an abstraction (like ``LLMProvider``) so the News Extractor and
its tests never depend on the network or a specific HTTP/HTML library. The HTML
parsing is separated from the network call so it can be unit-tested offline.
"""

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

    Raises:
        FetchError: If no readable text can be extracted.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - defensive
        raise FetchError("The 'beautifulsoup4' package is required to parse articles.") from exc

    soup = BeautifulSoup(html, "html.parser")

    # Drop non-content elements before reading text.
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paragraphs if p)
    if not text:
        # Fall back to the whole document text when there are no <p> tags.
        text = soup.get_text("\n", strip=True)

    text = text.strip()
    if not text:
        raise FetchError(f"No readable text found at {url}.")

    return FetchedArticle(url=url, title=title, text=text[:MAX_ARTICLE_CHARS])
