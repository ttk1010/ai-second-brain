# Issue #38: ログイン必須サイトの記事をブラウザ側キャプチャ→Inbox で KO 化

Labels: enhancement, parser, services

## Why
ログイン（無料会員登録を含む）が必要なサイト（例: @IT / ITmedia `atmarkit.itmedia.co.jp`）の記事から KO を生成したい。現状の News パイプラインは URL を ASB 自身が取得する前提（`HttpArticleFetcher`）で、認証の裏側にある本文は取得できない。

方針比較の結果、**B案（ブラウザ側キャプチャ→Inbox）**を採用する。**ASB は認証情報も Cookie も一切扱わず**、ユーザーが自分のログイン済みブラウザで取得した「本文テキスト＋元URL」を渡すだけにする。これにより ToS/秘密管理/JS 描画のリスクを負わず、ヘッドレスブラウザも不要（ADR 0004 の「ヘッドレス不採用」を維持）。ローカル・キャプチャの思想（ADR 0006）にも自然に乗る。

## Goal
「取得済みの本文テキスト＋元URL」を入力として受け取り、**フェッチをスキップして** News 抽出→KO 化する経路を追加する。KO パイプライン本体（抽出→教育設計→出力→保存）は無改修で、取得/キャプチャ層だけで閉じる。

## スコープ（今回）
- **入力経路1: Inbox スタブ**（主）。`00 Inbox/` に「frontmatter に `source:`（元URL）＋本文＝記事テキスト」のノートを置き、`asb-inbox` が captured 記事として処理する。
- **入力経路2: CLI**（副。ブックマークレット/スクリプト用）。`asb --captured-from <URL>` ＋ 本文を `--text-file` / 標準入力 / 位置引数で渡す。
- **ドキュメント**：Inbox キャプチャ書式、ワンクリックに近づけるためのブックマークレット例、セキュリティ方針（認証情報を ASB に渡さない）。
- News 種別として保存（`06 News`）、`source = 元URL`。冪等（#24）は URL 一致で効く。`--guidance`（#32）併用可。

## スコープ外（別 Issue）
- Cを主軸にした **セッション/Cookie 再利用フェッチャ**（自動取得）。JS サイト対応でヘッドレスが要るため ADR 0004 改訂を伴う。
- 完全自動ログイン（資格情報入力・MFA/CAPTCHA 自動化）。**やらない**。
- Telegram からの本文キャプチャ（`asb-capture` スキル拡張）。将来の追補。

## 提案する設計
- `NewsExtractor.extract_from_article(article, *, language, guidance)` を切り出し、`extract(url)` はフェッチ後にこれを呼ぶだけにする（captured 経路はフェッチを飛ばして直接呼ぶ）。
- `KnowledgePipeline.run_captured(url, text, *, title="", overwrite=False, guidance="")`：`FetchedArticle` を本文から構築→ NEWS 冪等チェック（url）→ `extract_from_article` → `from_news` → `_finalize`。News 抽出器が未構成なら `unsupported`。
- Inbox ワーカー：スタブの frontmatter に `source:`（http/https URL）＋本文が非空なら captured として `run_captured` に回す。従来のスタブ（1行の URL/概念）は現状どおり。
- CLI：`--captured-from <URL>` / `--text-file <path>` / `--title <t>` を追加。位置引数は任意化し、captured 時は本文を text-file→位置→stdin の順で解決。

### Inbox キャプチャ書式
```markdown
---
source: https://atmarkit.itmedia.co.jp/...
title: 記事タイトル   # 任意
---
（ここに記事本文をそのまま貼る）
```

## Tasks
- [ ] `NewsExtractor.extract_from_article` 切り出し（`extract` は委譲）
- [ ] `KnowledgePipeline.run_captured`（NEWS 冪等・guidance 記録・graceful degrade）
- [ ] Inbox ワーカーの captured スタブ判定＋処理（成功時にスタブ消費）
- [ ] `asb --captured-from`/`--text-file`/`--title` CLI
- [ ] README/docs：キャプチャ書式・ブックマークレット例・セキュリティ方針
- [ ] ADR：captured コンテンツ取り込み（認証は扱わない／ヘッドレス不採用維持）
- [ ] 単体テスト（extract_from_article、run_captured の created/dedup/unsupported/空入力、Inbox captured スタブ、CLI captured）。外部API/ネットワーク非依存

## Definition of Done
- ログイン必須サイトの記事でも、本文＋URL を渡せば KO が生成される（`06 News`、source=URL）
- ASB は認証情報・Cookie を一切扱わない。ヘッドレスブラウザを導入しない
- 冪等：同一 URL の再投入は再生成しない。`--guidance` 併用可
- 既存の URL/概念/比較の挙動は不変（後方互換）
- 外部API/ネットワーク非依存でテストが通る

## セキュリティ / 法務メモ
- 取得は「ユーザーが正規にアクセス権を持つコンテンツの個人利用」に限る。各サイトの ToS を確認。
- ペイウォール/CAPTCHA/MFA の回避はしない。ASB は資格情報を保存・入力しない。

## フェーズ / 扱い
取得/キャプチャ層の拡張。**マイルストーン無しの単独 enhancement**。ADR 0004（構造化抽出・ヘッドレス不採用）と ADR 0006（ローカル・キャプチャ）の延長で、両者と整合する。C案（セッション再利用）と D案（自動ログイン）は本 Issue のスコープ外。
