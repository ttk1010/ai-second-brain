# ADR 0009: ログイン必須サイトは「ブラウザ側キャプチャ→本文取り込み」で対応する

- Status: Accepted
- Date: 2026-07-19
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

ログイン（無料会員登録を含む）が必要なサイト（例: @IT / ITmedia）の記事から KO を生成したい（Issue #38）。現状の News パイプラインは URL を ASB 自身が `HttpArticleFetcher` で取得する前提で、認証の裏側にある本文は取れない。

AI エージェントがログイン必須サイトへアクセスする方法を検討した結果、次の緊張がある：
- ADR 0004 で「ヘッドレスブラウザ不採用・構造化ソース抽出」を決めている。
- 認証情報や Cookie を ASB が扱うと、秘密管理・利用規約・乗っ取り時のリスクを背負う。
- ペイウォール/CAPTCHA/MFA の自動回避は行うべきでない。

## Decision

### A. B案（ブラウザ側キャプチャ→本文取り込み）を採用する

ユーザーが**自分のログイン済みブラウザ**で得た「記事本文テキスト＋元URL」を ASB に渡し、**フェッチを飛ばして** News 抽出→KO 化する。ASB は**認証情報も Cookie も一切扱わない**。ヘッドレスブラウザも導入しない（ADR 0004 の方針を維持）。ローカル・キャプチャの思想（ADR 0006）の延長。

### B. 実装は取得/キャプチャ層に閉じ、KO パイプラインは不変

- `NewsExtractor.extract_from_article(article, ...)` を切り出し、`extract(url)` はフェッチ後にこれを呼ぶだけにする。captured 経路はフェッチを飛ばして直接呼ぶ。
- `KnowledgePipeline.run_captured(url, text, *, title, overwrite, guidance)`：本文から `FetchedArticle` を構築 → NEWS 冪等チェック（url）→ `extract_from_article` → `from_news` → `_finalize`。News 抽出器が未構成なら `unsupported`。
- News 種別として保存（`06 News`、`source = 元URL`）。冪等（#24）は URL 一致で効き、`--guidance`（#32）も併用可。

### C. 入力経路は Inbox（主）と CLI（副）

- **Inbox スタブ**：frontmatter に `source:`（http/https URL）＋本文＝記事テキスト。`asb-inbox` が captured として処理し、成功時にスタブを消費する。
- **CLI**：`asb --captured-from <URL>`（本文は `--text-file` / 位置引数 / 標準入力）。ブックマークレットやスクリプトから使える。

### D. スコープ外（別 Issue）

- セッション/Cookie 再利用フェッチャ（自動取得。JS サイト対応でヘッドレスが要るため ADR 0004 改訂を伴う）。
- 完全自動ログイン（資格情報入力・MFA/CAPTCHA 自動化）。**採用しない**。
- Telegram からの本文キャプチャ（`asb-capture` スキル拡張）。将来の追補。

## Consequences

- ログイン必須サイトの記事でも、本文＋URL を渡せば KO が生成できる。ASB は認証を扱わず、規約・秘密管理・JS 描画のリスクを負わない。
- 取得層の追加だけで完結し、抽出→教育設計→出力→保存は無改修（`ArticleFetcher` 抽象と `from_news` の対称性の恩恵）。
- 手間はユーザー側に残る（本文をコピーして Inbox/CLI に渡す）。ブックマークレットで軽減する。
- 本文の正確さはユーザーのキャプチャに依存する（ASB は渡されたテキストを信頼して要約する）。

## Alternatives considered

- **セッション/Cookie 再利用フェッチャ（C案）**：自動度は高いが、JS サイトでヘッドレスが要り ADR 0004 の改訂を伴う。まず認証を扱わない B案を出し、必要になってから別 Issue で検討。
- **完全自動ログイン（D案）**：脆く、規約・セキュリティのリスクが高く、MFA/CAPTCHA で破綻。資格情報の自動入力は行わない。
- **公式チャネル（RSS/API）のみ**：安全だが、ログインゲート記事という当初要望を満たさない。無料記事の取得は既存の URL 経路で従来どおり可能。
