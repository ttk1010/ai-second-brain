"""Tests for the ledge.ai access-ranking parser (Issue #39).

The fixture mimics ledge.ai's Nuxt 2 IIFE payload: one ranking item inlined, one
with field-level parameter references (title/slug minified to params), so the
resolver is exercised without any network access.
"""

from backend.parser.ranking import RankedArticle, parse_ledge_monthly_rankings

_NUXT = (
    "window.__NUXT__=(function(a,t2,s2){return {x:[{monthlyAccessRankings:["
    '{rank_order:1,article:{data:{id:1,attributes:{title:"見出し1：Aの話",slug:"slug-1"}}}},'
    "{rank_order:2,article:{data:{id:2,attributes:{title:t2,slug:s2}}}}"
    ']}]}}(null,"見出し2：Bの話","slug-2"))'
)
FIXTURE_HTML = f"<html><body><script>{_NUXT}</script></body></html>"


def test_parses_ranking_in_order_with_urls() -> None:
    ranked = parse_ledge_monthly_rankings(FIXTURE_HTML)

    assert ranked == [
        RankedArticle(rank=1, title="見出し1：Aの話", url="https://ledge.ai/articles/slug-1"),
        RankedArticle(rank=2, title="見出し2：Bの話", url="https://ledge.ai/articles/slug-2"),
    ]


def test_resolves_field_level_parameter_references() -> None:
    # The second item's title/slug are parameter refs (t2, s2), not literals.
    ranked = parse_ledge_monthly_rankings(FIXTURE_HTML)
    assert ranked[1].title == "見出し2：Bの話"
    assert ranked[1].url.endswith("/slug-2")


def test_limit_caps_the_result() -> None:
    assert len(parse_ledge_monthly_rankings(FIXTURE_HTML, limit=1)) == 1


def test_returns_empty_when_ranking_absent() -> None:
    assert parse_ledge_monthly_rankings("<html><body>no ranking here</body></html>") == []
