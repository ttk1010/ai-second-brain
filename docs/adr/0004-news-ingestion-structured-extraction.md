# ADR 0004: News 取り込み — 構造化ソース抽出チェーン、ヘッドレスブラウザ不採用

- Status: Accepted
- Date: 2026-06-28
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

Phase 2 で URL 入力（News パイプライン）を実装した。当初の `HttpArticleFetcher` は静的 HTML の `<p>` 抽出のみだったが、実 API テストで主対象サイト（ledge.ai）が **Nuxt 製 SPA** で本文が静的 HTML に無く、ナビ/関連記事の断片しか取れず要約品質が著しく低下することが判明した。

JS レンダリング記事の本文をどう取得するか、また News 抽出結果を Knowledge Object にどうマッピングするかを決める必要がある。コスト方針として重い依存（ヘッドレスブラウザ）は避けたい。

## Decision

### A. 本文抽出は構造化ソース優先の戦略チェーン

`parse_article` は次の順で最初に有効な本文を採用する:

1. JSON-LD `NewsArticle.articleBody`（多くのニュースサイトが持つ標準）
2. Nuxt `window.__NUXT__` の `content` フィールド（ledge.ai 等。最長の content を本文とみなし、JS エスケープ解除と markdown ディレクティブ除去を行う）
3. 静的 `<p>` 抽出（従来のフォールバック）

### B. ヘッドレスブラウザは導入しない

Playwright 等のヘッドレスブラウザは導入せず、**ページに埋め込まれた構造化データから抽出**する。当面の主対象は ledge.ai。将来は他サイト向け戦略をチェーンに追加して拡張する。

### C. NewsExtraction は ConceptExtraction と対称な形にする

News 抽出結果は Concept 抽出と同じ形（title / summary / background / key_takeaways / concepts / entities / references）に揃える。ARCHITECTURE の News 観点（technology / companies / impact）は次のように対応づけ、**Knowledge Object のスキーマを安易に拡張しない**:

- technology → `concepts`
- companies / people → `entities`
- impact → `summary` に織り込む（専用フィールドは作らない）

これにより Builder の正規化（`from_concept` / `from_news`）が対称になり、下流は入力種別を意識しない。

## Consequences

- ledge.ai を含む JS レンダリング記事から本文を取得でき、要約品質が回復した（実 API で検証済み）。
- 重い依存・ブラウザバイナリ・実行時間の増大を避けられ、CI もオフラインのまま保てる（HTML 解析は固定フィクスチャでテスト）。
- Nuxt `content` 抽出はサイト構造に依存するため、ledge.ai 側の実装変更で壊れうる。戦略チェーンなので静的 `<p>` にフォールバックはするが、サイト個別対応は保守項目として残る。
- impact を構造化データとして保持しないため、将来 impact を個別に扱いたくなった場合はスキーマ拡張（別 ADR）が必要。

## Alternatives considered

- **ヘッドレスブラウザ（Playwright）で描画してから抽出**: 汎用的だが、重い依存・ブラウザ管理・低速化・CI 複雑化を招く。「ledge.ai 念頭・低コスト」という要件に反するため不採用。
- **News 専用に Knowledge Object へ impact 等のフィールドを追加**: CLAUDE.md「スキーマを安易に増やさない」に反し、Concept との対称性も崩れるため不採用。summary に織り込む。
