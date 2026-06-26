# Issue #19: News Fetcher 強化（JSレンダリング記事の本文抽出）

Labels: enhancement, parser
Milestone: (none — News pipeline hardening)

## Why
`HttpArticleFetcher` は静的HTMLの `<p>` 抽出前提のため、JSレンダリングのニュースサイトでは本文が取れない。実APIテストで ledge.ai 記事を処理したところ、本文ではなくサイトのナビ/関連記事の断片しか抽出できず、要約品質が著しく低下した（モデルが "the body text provided is incomplete" と明記）。よく使う予定の ledge.ai をまず対象にする。

## 調査結果（ledge.ai）
- Nuxt 製SPA（`window.__NUXT__` あり）。JSON-LD / OGタグなし。
- 記事本文は `__NUXT__` 内の唯一の `content:"..."` フィールドに markdown 形式で格納（約4.4KB、`:::small` ディレクティブや `[text](url){target}` 形式のリンクを含む）。

## Goal
JSレンダリング記事でも本文を抽出できるようにする。ヘッドレスブラウザ等の重い依存は導入せず、ページに埋め込まれた構造化データから本文を取得する。

## Tasks
- [ ] 抽出を戦略チェーン化：(1) JSON-LD `NewsArticle.articleBody`、(2) Nuxt `__NUXT__` の `content`、(3) 既存の `<p>` 抽出、の順で最初に有効な本文を採用
- [ ] Nuxt `content` 抽出：`__NUXT__` から `content` を取り出し、JSエスケープ解除＋ markdown ディレクティブ（`:::...`、`{...}` 属性）の除去で読みやすいテキスト化
- [ ] 既存の文字数上限・空本文時のエラーは維持
- [ ] サンプルHTML（ledge.ai 由来の固定フィクスチャ）でオフラインの単体テスト（ネットワーク非依存）

## Definition of Done
- ledge.ai 記事の本文が抽出され、要約に十分なテキストが得られる
- JSON-LD を持つ一般的なニュースサイトでも本文が取れる
- 静的HTMLサイトは従来どおり動作（後方互換）
- 重い依存（ヘッドレスブラウザ）を増やさない
- オフラインでテストが通る

## Notes
- 当面の主対象は ledge.ai。将来的に他サイトの戦略を追加しやすい構造にする。
