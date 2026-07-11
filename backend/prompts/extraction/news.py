"""News extraction prompt.

- Version: 2
- Purpose: Turn a fetched news article (any field, AI by default) into structured
  knowledge fields.
- Expected input: an article's title and body text (already fetched).
- Expected output: a JSON object with title, summary, concepts, entities,
  references (see NEWS_OUTPUT_SCHEMA).

Prompts are first-class assets and live here, never embedded in application code
(PROMPT_STYLE_GUIDE.md). The News pipeline produces the same normalized fields as
the Concept pipeline so downstream components stay input-agnostic (ARCHITECTURE.md).
It is domain-independent: it handles any field, with AI as the default focus
(ADR 0008).
"""

from backend.parser.fetcher import FetchedArticle
from backend.prompts.domain import DEFAULT_READER
from backend.prompts.guidance import guidance_directive
from backend.prompts.language import language_directive

NEWS_SYSTEM_PROMPT = f"""\
You are an educational knowledge extractor for a personal knowledge base.
You are given a news article. Turn it into reusable knowledge for a reader who
may not know this specific story. {DEFAULT_READER}

Follow these rules:
- Infer the field/domain the story belongs to; do not assume it is about AI.
- Be factual; rely only on the article, do not invent details.
- The summary must cover what happened, what it involves (the technology, method,
  or subject), the organizations or people involved, and why it matters (its impact).
- "concepts" are the topics/technologies involved; "entities" are the
  organizations, products, or people named.
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
  "domain": "string, the field this belongs to (e.g. 'AI', '政治'); use 'AI' if AI-related",
  "published_date": "string, the article's publication date as YYYY-MM-DD, or empty if unknown",
  "summary": "string, 3-5 sentences covering what happened, the technology, the
    companies/people, and why it matters",
  "background": "string, 2-4 sentences on the context behind this story and why it matters",
  "key_takeaways": ["string, 3-5 points a reader should remember"],
  "concepts": ["string, technologies or topics involved"],
  "entities": ["string, organizations, models, or people involved"],
  "references": ["string, source URLs; include the article URL"]
}
"""


def build_news_user_prompt(
    article: FetchedArticle, *, language: str = "ja", guidance: str = ""
) -> str:
    """Build the user prompt for extracting knowledge from a news article."""
    return (
        f"Source URL: {article.url}\n"
        f"Article title: {article.title}\n\n"
        f"Article text:\n{article.text}\n\n"
        f"{NEWS_OUTPUT_SCHEMA}\n"
        f"{language_directive(language)}"
        f"{guidance_directive(guidance)}"
    )
