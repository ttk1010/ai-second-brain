"""News extraction prompt.

- Version: 1
- Purpose: Turn a fetched AI news article into structured knowledge fields.
- Expected input: an article's title and body text (already fetched).
- Expected output: a JSON object with title, summary, concepts, entities,
  references (see NEWS_OUTPUT_SCHEMA).

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The News pipeline produces the same normalized fields as
the Concept pipeline so downstream components stay input-agnostic (ARCHITECTURE.md).
"""

from backend.parser.fetcher import FetchedArticle
from backend.prompts.language import language_directive

NEWS_SYSTEM_PROMPT = """\
You are an educational knowledge extractor for an AI knowledge base.
You are given an AI-related news article. Turn it into reusable knowledge for a
software engineer who follows AI but may not know this specific story.

Follow these rules:
- Be factual; rely only on the article, do not invent details.
- The summary must cover what happened, the technology involved, the companies or
  people involved, and why it matters (its impact).
- "concepts" are the AI technologies/topics; "entities" are the organizations,
  models, or people named.
- Prefer conceptual clarity over jargon.
- Respond with a single JSON object only. Do not include prose outside the JSON.

For "short_title", give a concise note filename: the key entity and the core
topic, dropping marketing words and secondary details, keeping product/version
names. Examples (full title -> short_title):
- "Sakana AI、…「Sakana Fugu」提供開始 一部…" -> "Sakana Fugu"
- "画像生成AIのMidjourney、医療ハードウェアに参入 …" -> "Midjourney、医療ハードウェアに参入"
- "IBM、1nm未満世代のチップ技術を発表 …" -> "IBM、1nm未満世代のチップ"
- "OpenAI、GPT-5.6を発表 最上位「Sol」…" -> "GPT-5.6"
"""

NEWS_OUTPUT_SCHEMA = """\
Return a JSON object with exactly these fields:
{
  "title": "string, the article's full descriptive title",
  "short_title": "string, concise filename: key entity + core topic (see rules above)",
  "summary": "string, 3-5 sentences covering what happened, the technology, the
    companies/people, and why it matters",
  "background": "string, 2-4 sentences on the context behind this story and why it matters",
  "key_takeaways": ["string, 3-5 points a reader should remember"],
  "concepts": ["string, AI technologies or topics involved"],
  "entities": ["string, organizations, models, or people involved"],
  "references": ["string, source URLs; include the article URL"]
}
"""


def build_news_user_prompt(article: FetchedArticle, *, language: str = "ja") -> str:
    """Build the user prompt for extracting knowledge from a news article."""
    return (
        f"Source URL: {article.url}\n"
        f"Article title: {article.title}\n\n"
        f"Article text:\n{article.text}\n\n"
        f"{NEWS_OUTPUT_SCHEMA}\n"
        f"{language_directive(language)}"
    )
