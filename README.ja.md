# AI Second Brain

> Capture. Understand. Visualize. Remember.

[English](README.md) · **日本語**

[![CI](https://github.com/ttk1010/ai-second-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/ttk1010/ai-second-brain/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

<p align="center">
  <img src="docs/assets/cover.png" width="820"
       alt="CLI・Claudeモバイルアプリ・Telegram など、どこからでも入力を送ると、AI Second Brain が構造化Markdownノート・教育イラスト・Obsidian風のリンクグラフに変換する。">
</p>

<p align="center"><sub>カバー画像は AI Second Brain の画像生成エンジン（gpt-image-2）で作成。</sub></p>

## これは何？

AI Second Brain は、学んだことを **構造化された・視覚的な・成長し続ける知識ベース**
に変えるツールです。概念（`Transformer`）・記事URL・比較（`GPT, Claude, Gemini`）を
渡すと、[Obsidian](https://obsidian.md/) の Vault に **イラスト付きの構造化Markdown
ノート**を生成し、知識グラフに繋ぎます。AI をデフォルトの重点分野としつつ、あらゆる
分野（生物・経済・料理…）を扱え、各ノートにドメインをタグ付けします（ADR 0008）。

本当の成果物はノートや画像ではなく、**整理された再利用可能な知識**です。すべての出力は
1つの正規表現である [Knowledge Object](docs/DATA_MODEL.md) から生成されるため、ノートの
一貫性が保たれ、AI ツールが無くても Vault は価値を持ち続けます。

> 📖 README は日本語・英語の2言語。詳細な設計ドキュメント（`docs/`・ADR）は**日本語**で
> 書かれています。

## 例

```bash
uv run asb "LLM"
```

を実行すると、Vault に `01 Concepts/大規模言語モデル.md` が生成されます。イラストを埋め込み、
リンクを解決した完全なノートです：

```markdown
---
title: "大規模言語モデル"
source_type: concept
tags: [Transformer, Generative AI, Foundation Model, RAG, Attention, ...]
---

# 大規模言語モデル

## Summary
大規模言語モデル（LLM）は、大量のテキストを学習して、自然言語のパターンを
予測・生成するAIモデルです。…

## Illustration
![[Images/LLM.png]]

## Key Takeaways
- LLMは大量のテキストから言語の統計的パターンを学び、次の語を予測する…
- 高い汎用性があり、プロンプトや追加学習によって多様なタスクに適応できる…

## Related Notes
- [[AIエージェント]] — application
- [[RAG]] — application
- [[埋め込み]] — related
```

（ノートは設定した言語で生成されます。既定は日本語です。）

## 必要なもの

- **Python 3.12** と [uv](https://docs.astral.sh/uv/)。
- **OpenAI API キー — 必須。** ノート生成は OpenAI API（テキスト＝`gpt-5.4`、イラスト＝
  `gpt-image-2`）を呼ぶため、**ノートごとに従量課金**されます。画像生成が主なコストで、
  同じ入力の再実行はスキップ（再課金なし）、`--no-image` でイラストを省いて節約できます。
- **Claude サブスクリプション ＋ [Claude Code](https://www.claude.com/product/claude-code) — 任意。**
  `asb-relink`（リンクスキル）と Telegram キャプチャ（Claude Code Channels）にのみ必要で、
  中核の `asb` コマンドには不要です。

## クイックスタート

[uv](https://docs.astral.sh/uv/) と Python 3.12 が必要（上記「必要なもの」参照）。

```bash
# 1. 依存関係のインストール
uv sync --dev

# 2. 設定：vault_path を Obsidian Vault に向け、APIキーを設定
cp config/settings.example.toml config/settings.toml   # vault_path を編集
echo 'OPENAI_API_KEY=sk-...' > .env

# 3. ノートを生成
uv run asb "Transformer"                 # 概念
uv run asb "https://ledge.ai/..."        # ニュース記事
uv run asb --compare "GPT, Claude, Gemini"   # 比較

# --guidance でトーン・対象読者・強調点を指示
uv run asb "Transformer" --guidance "高校生向けに、歴史的背景を含めて"

# 1枚ではなく複数ページの解説イラストにする
uv run asb "Transformer" --pages 4      # ちょうど4ページ（観点ごと）
uv run asb "Transformer" --pages auto   # プランナーが枚数を決定（2〜6）
```

各ノートは教育イラスト付きで Vault に書き込まれます。同じ入力の再実行は no-op
（`--overwrite` で再生成、`--no-image` でイラストを省略）。

`--guidance "<自然文>"` は、ノート本文**と**イラストの両方を steer する自由記述の指示
（トーン・対象読者・どの角度を強調するか）で、ノートのフロントマターに記録されます。
冪等性は変わらず、`--overwrite` を付けない限り同じ入力はスキップされます（新しい guidance
で作り直せます）。

`--pages {N|auto}` は、1枚のイラストを **観点ごとの複数ページシリーズ**（全体像→仕組み→
具体例→注意点）にします。全ページが同一スタイルで、2枚目以降は1枚目を参照画像として生成
されます。オプトインで、付けなければ従来どおり1枚。**各ページは別の画像API呼び出しなので
`--pages N` は画像生成が N 倍**（上限6ページ）。`--no-image` が最優先で何も生成しません。
[ADR 0012](docs/adr/0012-multi-page-illustration.md) を参照。

### 既存ノートのリビジョン

ノート全体を作り直さず、一部だけ改善します：

```bash
asb-revise "Transformer" "要約をもっと易しく"            # 本文セクションを書き直す
asb-revise "AWS" "図を白背景で描き直して" --illustration   # イラストを描き直す
asb-revise "AWS" "背景を厚く" --section background        # セクションを明示指定
```

`asb-revise` はタイトル/ファイル名でノートを探し、対象の本文セクション
（`summary` / `background` / `key_takeaways`）だけを書き直すか、既存画像を参照に
イラストを描き直します（テイストを保ち、指示した箇所だけ変わる）。`--section` /
`--illustration` を付けなければ指示文から対象を推定します。変更はその場に書き込まれ、
Vault は Git 管理なので履歴はそこに残ります。[ADR 0014](docs/adr/0014-note-revision.md) を参照。

## 主な機能

- **3つの知識タイプ：** AI **概念**、**ニュースURL**（取得・要約。JS描画サイトも）、**比較**（表付き）。
- **教育イラスト：** ノートごとに一貫した手描きビジュアル（gpt-image-2）。`--pages` で複数ページ化も可能。
- **構造化Markdownノート：** 要約・背景・キーポイント・関連ノート・出典・タグ。AIツール無しでも読める。
- **自然言語リビジョン：** `asb-revise` で既存ノートの1セクションやイラストをその場で改善。
- **自動リンク：** `asb-relink`（Claude Code スキル）がノートをグラフに接続（OpenAI課金ゼロ）。バックリンクは Obsidian から。
- **どこからでもキャプチャ：** ローカルの `00 Inbox` キュー（`asb-inbox`）と、Claude Code Channels（Telegram）経由のチャットキャプチャ。ローカルファースト・固定ホスティング費ゼロ。
- **外出先からの即時生成（任意）：** AWS Lambda エンドポイントがクラウドで同じパイプラインを実行し、ノートを Git 管理の Vault にコミット。Mac がオフでもスマホから生成できる（インフラ費はほぼ無料・ゼロスケール）。手順：[DEPLOY_SERVERLESS.md](docs/DEPLOY_SERVERLESS.md)、設計：[ADR 0015](docs/adr/0015-serverless-instant-generation.md)。
- **月次ダイジェスト：** `asb-digest` が [ledge.ai](https://ledge.ai/) の30日アクセスランキングを1枚のノート＋俯瞰イラストにまとめる。

## 仕組み

```
URL / Concept / Comparison
        │
        ▼
  Input Classifier ──▶ Extractor (LLM)
        │
        ▼
  Knowledge Object  ← 唯一の source of truth
        │
        ▼
 Educational Planner
        │
        ├──▶ Markdown Generator
        ├──▶ Illustration Generator (gpt-image-2)
        └──▶ Knowledge Linker
        │
        ▼
   Obsidian Vault (external)
```

すべてが Knowledge Object を通るので、新しい出力形式も同じ正規表現を消費します。
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)、[docs/DATA_MODEL.md](docs/DATA_MODEL.md)、
before/after 図の [docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md) を参照。

Obsidian Vault はこのリポジトリの**外**（`vault_path` で設定）にあります。本リポジトリは
コードとドキュメントのみを管理し、知識データは決して含みません（[ADR 0002](docs/adr/0002-vault-and-layout.md)）。

## ノートを繋ぐ

Vault が育ったら、ノードを知識グラフに繋ぎます：

- **`asb-link`**（決定論的・無料）：Vault をインデックスし、ノートの「Related Notes」セクションを安全に書き換える。
- **`asb-relink`（Claude Code スキル）**（賢い・OpenAI課金ゼロ）：Vault 全体を読み、どのノートが関連するか（どう繋がるか）を判断してリンクを適用。OpenAI API ではなく Claude サブスクリプションを使う。

## どこからでもキャプチャ

キャプチャと処理はキューで分離され、すべてローカルで動くため固定ホスティング費が
かかりません（[ADR 0006](docs/adr/0006-capture-interface-local-first.md)）。

- **Inbox キュー：** Obsidian から `00 Inbox/` に URL や概念のスタブを置き、`uv run asb-inbox` でまとめてノート化。
- **チャットキャプチャ（Telegram）：** [Claude Code Channels](https://code.claude.com/docs/en/channels) 経由で bot にメッセージ → 手元の Claude Code が `asb` を実行して返信。手順は [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md)。
- **スマホから即時（任意）：** AWS Lambda エンドポイントが Mac オフでもクラウドで生成。iOS ショートカットから起動。手順は [docs/DEPLOY_SERVERLESS.md](docs/DEPLOY_SERVERLESS.md)。

### ログイン必須サイト（キャプチャ済みコンテンツ）

`asb` が取得できないログイン背後（無料会員ウォール含む）のページは、**自分のログイン済み
ブラウザから本文テキストを持ち込みます** — Inbox スタブ、`asb --captured-from <URL>`、または
Claude in Chrome 拡張で Claude Code がページを読む方式。ASB は認証情報やクッキーを一切
扱わず、渡されたテキストを要約して News として source URL の下に保存します
（[ADR 0009](docs/adr/0009-captured-content-ingestion.md)）。詳細は
[docs/CAPTURED_CONTENT.md](docs/CAPTURED_CONTENT.md)。

## 月次ダイジェスト

`asb-digest` はその月の話題の AI ニュースを1枚に俯瞰します。[ledge.ai](https://ledge.ai/) の
**30日アクセスランキング**を読み、各記事を一文要約し、`08 Digests` にダイジェストノート＋
俯瞰イラストを生成します（[ADR 0010](docs/adr/0010-monthly-news-digest.md)）。

```bash
uv run asb-digest                       # 今月・トップ10（全自動）
uv run asb-digest --month 2026-08 --top 5
```

**高品質版（Claude Code）：** `asb-digest` スキルは実際の記事本文を読んでラベル/要約を
自分で執筆します — より良いキャプション、かつ **OpenAI テキスト課金ゼロ**（画像のみ課金。
[ADR 0011](docs/adr/0011-digest-claude-authored-labels.md)）。

## 思想

このプロジェクトは画像ジェネレータでもノートアプリでもなく、**知識オペレーティングシステム**
です。画像・Markdown・Git は出力に過ぎず、成果物は整理された知識です。指針：

- **コンテンツより知識** — 投稿ではなく再利用可能な知識を作る。
- **創造性より一貫性** — 同じ概念は常に同じように説明・描画される。
- **人間の制御下での自動化** — 繰り返し作業は自動化し、知識の品質は人間が持つ。
- **長期の保守性** — すべての決定は数年後も意味を持つべき。

全体像と長期ゴールは [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md) に。

## ドキュメント

設計ドキュメントは日本語、README は2言語です。

| ドキュメント | 目的 |
|----------|---------|
| [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md) | ビジョンと長期ゴール |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | システムアーキテクチャ |
| [docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md) | before/after 構成図 |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Knowledge Object スキーマ |
| [docs/DEPLOY_SERVERLESS.md](docs/DEPLOY_SERVERLESS.md) | サーバーレス即時生成のデプロイ手順 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 開発ロードマップ |
| [docs/CAPTURED_CONTENT.md](docs/CAPTURED_CONTENT.md) | ログイン必須記事のキャプチャ |
| [docs/adr/](docs/adr/) | Architecture Decision Records |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | セットアップ・実行時のトラブルシューティング |
| [CLAUDE.md](CLAUDE.md) | AI 支援開発のエンジニアリングガイド |

## ロードマップと状況

🚧 開発中。**Phase 1–4 完了**（基盤・教育コンテンツ・知識整理・ローカルファーストキャプチャ）。
最近の追加：**複数ページイラスト**（`--pages`）、**自然言語リビジョン**（`asb-revise`）、
**サーバーレス即時生成（任意）**（スマホから生成）。**Phase 5 — AI リサーチアシスタント**が次です。
[docs/ROADMAP.md](docs/ROADMAP.md) を参照。

## コントリビュート

コントリビュート歓迎です。小さく・レビュー可能で・Issue 駆動の変更を好みます。
[CONTRIBUTING.md](CONTRIBUTING.md)（英語）を参照。

## ライセンス

[MIT](LICENSE) © 2026 ttk1010
