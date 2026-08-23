"""Access-ranking fetcher for the monthly digest (Issue #39).

Extracts ledge.ai's "30日間アクセスランキング" (30-day access ranking) — the
ready-made importance signal for the monthly digest. The ranking is not in the
static markup; it lives in the inline ``window.__NUXT__`` payload (a Nuxt 2 IIFE
that minifies repeated values into function-parameter references). We rebuild the
parameter environment and resolve each ranked article's title and slug down to
its field-level references, so no headless browser is needed (ADR 0004 stands).

This parsing is ledge.ai-specific and depends on that serialization; if the site
changes it, the fetcher returns an empty list and the caller degrades gracefully
(ADR 0009 / ADR 0004 accept this maintenance cost).
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.parser.fetcher import FetchError

LEDGE_HOME_URL = "https://ledge.ai/"
LEDGE_ARTICLE_BASE = "https://ledge.ai/articles/"
DEFAULT_TOP_N = 10


@dataclass(frozen=True)
class RankedArticle:
    """One entry in an access ranking: its position, title, and URL."""

    rank: int
    title: str
    url: str


class RankingFetcher(ABC):
    """Abstract source of a news access ranking."""

    @abstractmethod
    def fetch_monthly(self, *, limit: int = DEFAULT_TOP_N) -> list[RankedArticle]:
        """Return the 30-day access ranking, most-accessed first."""


class LedgeAiRankingFetcher(RankingFetcher):
    """Fetches ledge.ai's 30-day access ranking from its homepage."""

    def __init__(self, *, timeout: float = 15.0, user_agent: str = "AI-Second-Brain/0.1") -> None:
        self._timeout = timeout
        self._user_agent = user_agent

    def fetch_monthly(self, *, limit: int = DEFAULT_TOP_N) -> list[RankedArticle]:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - defensive
            raise FetchError("The 'httpx' package is required for LedgeAiRankingFetcher.") from exc

        try:
            response = httpx.get(
                LEDGE_HOME_URL,
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": self._user_agent},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FetchError(f"Failed to fetch ledge.ai homepage: {exc}") from exc

        return parse_ledge_monthly_rankings(response.text, limit=limit)


def parse_ledge_monthly_rankings(html: str, *, limit: int = DEFAULT_TOP_N) -> list[RankedArticle]:
    """Parse the 30-day ranking (title + URL) from a ledge.ai homepage.

    Returns up to ``limit`` articles in rank order, or an empty list when the
    ranking cannot be located (the caller degrades gracefully).
    """
    env = _build_nuxt_env(html)
    region = _array_region(html, "monthlyAccessRankings:")
    if region is None:
        return []

    ranked: list[RankedArticle] = []
    for item in _split_top(region[1:-1]):
        match = re.search(r"article:(\{.*|\w+)$", item.strip(), re.S)
        if not match:
            continue
        article = _deref(match.group(1), env)
        data = _deref(_object_field(article, "data") or "", env)
        attributes = _deref(_object_field(data, "attributes") or "", env)
        title = _string_value(_object_field(attributes, "title") or "", env)
        slug = _string_value(_object_field(attributes, "slug") or "", env)
        if title and slug:
            ranked.append(
                RankedArticle(rank=len(ranked) + 1, title=title, url=f"{LEDGE_ARTICLE_BASE}{slug}")
            )
        if len(ranked) >= limit:
            break
    return ranked


# --- Nuxt 2 IIFE payload helpers ------------------------------------------------


def _build_nuxt_env(html: str) -> dict[str, str]:
    """Rebuild the ``window.__NUXT__`` IIFE's parameter -> value environment."""
    marker = "window.__NUXT__=(function("
    start = html.find(marker)
    if start == -1:
        return {}
    p_open = html.index("(", start + len("window.__NUXT__=(function"))
    p_close = _matching(html, p_open, "(", ")")
    body_open = html.index("{", p_close)
    body_close = _matching(html, body_open, "{", "}")
    arg_open = html.index("(", body_close)
    arg_close = _matching(html, arg_open, "(", ")")
    if -1 in (p_close, body_close, arg_close):
        return {}

    params = [p.strip() for p in html[p_open + 1 : p_close].split(",")]
    args = [a.strip() for a in _split_top(html[arg_open + 1 : arg_close])]
    return dict(zip(params, args, strict=False))


def _array_region(text: str, key: str) -> str | None:
    """Return the ``[...]`` array literal that follows ``key``, or None."""
    start = text.find(key)
    if start == -1:
        return None
    open_idx = text.index("[", start)
    close_idx = _matching(text, open_idx, "[", "]")
    if close_idx == -1:
        return None
    return text[open_idx : close_idx + 1]


def _matching(text: str, i: int, open_c: str, close_c: str) -> int:
    """Index of the bracket matching ``text[i]``, respecting string literals."""
    depth = 0
    quote = ""
    escaped = False
    for j in range(i, len(text)):
        c = text[j]
        if quote:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == quote:
                quote = ""
            continue
        if c in "\"'":
            quote = c
        elif c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return j
    return -1


def _split_top(text: str) -> list[str]:
    """Split ``text`` on top-level commas, respecting brackets and strings."""
    out: list[str] = []
    depth = 0
    quote = ""
    escaped = False
    start = 0
    for j, c in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == quote:
                quote = ""
            continue
        if c in "\"'":
            quote = c
        elif c in "[{(":
            depth += 1
        elif c in "]})":
            depth -= 1
        elif c == "," and depth == 0:
            out.append(text[start:j])
            start = j + 1
    out.append(text[start:])
    return out


def _deref(token: str, env: dict[str, str]) -> str:
    """Resolve a bare parameter reference to its value (following chains)."""
    token = token.strip()
    for _ in range(8):
        if re.fullmatch(r"[A-Za-z]\w?", token) and token in env:
            token = env[token].strip()
        else:
            break
    return token


def _string_value(token: str, env: dict[str, str]) -> str:
    """Resolve a field token to a plain string (literal or parameter ref)."""
    token = _deref(token, env)
    match = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', token)
    if not match:
        return "" if token in {"", "a"} else token  # 'a' is Nuxt's void/null param
    return match.group(1)


def _object_field(obj: str, field: str) -> str | None:
    """Return the raw value token for ``field`` in an object literal, or None."""
    match = re.search(field + r":", obj)
    if not match:
        return None
    rest = obj[match.end() :].lstrip()
    if rest.startswith('"'):
        m = re.match(r'"((?:[^"\\]|\\.)*)"', rest)
        return m.group(0) if m else None
    if rest.startswith("{"):
        end = _matching(rest, 0, "{", "}")
        return rest[: end + 1] if end != -1 else None
    m = re.match(r"[A-Za-z]\w?", rest)
    return m.group(0) if m else None
