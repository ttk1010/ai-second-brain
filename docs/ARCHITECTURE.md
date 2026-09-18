# システムアーキテクチャ

Version: 1.0

Status: Draft

---

# 目的

このドキュメントは、AI Second Brain の高レベルなアーキテクチャを定義する。

情報がシステム内をどう流れ、各コンポーネントが生の入力を使いまわせる知識へと変換する
うえでどんな責務を持つかを説明することを目的とする。

実装の詳細はソースコードに属する。

このドキュメントは、アーキテクチャ・責務・データフローに焦点を当てる。

現在のローカルファースト設計と、提案中の AWS Lambda サーバーレス設計の before/after 構成図は
[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) を参照。

---

# 設計原則

アーキテクチャは次の原則を満たすべきである。

* 賢さより単純さ
* モノリシックよりモジュラー
* 知識を第一に（Knowledge-first）
* 人間が読める出力
* AI 依存ではなく AI 支援
* 拡張しやすいこと

各コンポーネントは単一の責務を持つべきである。

---

# 高レベルアーキテクチャ

```
                        User
                          │
                          ▼
          URL / AI Concept / News
                          │
                          ▼
                 Input Classifier
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
   Concept Extractor               News Extractor
          │                               │
          └───────────────┬───────────────┘
                          ▼
              Knowledge Object Builder
                          │
                          ▼
                  Knowledge Object
                          │
                          ▼
               Educational Planner
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
Markdown Generator  Illustration Generator  Metadata Generator
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                 Knowledge Linker
                          │
                          ▼
                  Knowledge Node
                          │
                          ▼
                  Obsidian Vault
                          │
                          ▼
                    Git Repository
                          │
                          ▼
                        GitHub
```

---

# 中核コンポーネント

## 1. 入力レイヤー（Input Layer）

### 責務

ユーザー入力を受け取る。

対応する入力：

* AI の概念
* URL
* 論文
* ニュース記事

入力レイヤーはきわめて軽量なままであるべきである。

その唯一の役割は、入力を受け付けることである。

---

## 2. Input Classifier（入力の分類）

### 責務

入力の種類を判定する。

想定される分類ラベル：

* Concept
* News
* Research Paper
* Documentation
* Unknown

Phase 1 では、これらのラベルは 2 つの処理パイプラインにのみ対応づく（ADR 0001 参照）。

* Concept → Concept パイプライン
* News → News パイプライン
* Research Paper / Documentation → 暫定的に News パイプラインで扱う（URL 入力として処理）
* Unknown → URL として解釈できれば News パイプラインにフォールバック。そうでなければ、明示的な
  エラーで即座に失敗する

Research Paper と Documentation の専用パイプラインは、将来の Issue に先送りする。

---

## 3. 知識パイプライン（Knowledge Pipelines）

入力の種類ごとに、異なる処理が必要になる。

例：

### Concept パイプライン

入力：

Transformer

出力：

* 概念の説明
* 関連概念
* 教育的な構造

---

### News パイプライン

入力：

https://ledge.ai/...

出力：

* 要約
* 技術
* 企業
* 影響
* 関連概念

どちらのパイプラインも、最終的には同じ正規化された構造を生む。

---

# Knowledge Object Builder

このコンポーネントは、すべての入力を正本の内部表現である **Knowledge Object** に変換する。
正規化を担う唯一のコンポーネントである。

正式なスキーマは `DATA_MODEL.md` で定義される。Knowledge Object は次のフィールドで構成される。

```text
KnowledgeObject
├── id
├── source
├── title
├── summary
├── concepts
├── entities
├── relationships
├── educational_plan
├── references
├── metadata
└── outputs (optional)
```

下流のコンポーネントは、元の入力がキーワードだったか URL だったかを気にすべきではない。

> 注：初期の草案ではこのコンポーネントを「Knowledge Normalizer」と呼んでいた。名称は
> **Knowledge Object Builder** に統一された（ADR 0001）。データ構造の詳細は `DATA_MODEL.md`
> が source of truth である。

---

# Educational Planner

これはシステムの心臓部である。

その責務は要約ではない。

その責務は教育である。

次を決める。

* 何を説明すべきか？
* 何を可視化すべきか？
* どの概念を強調すべきか？
* どんな前提知識を想定すべきか？

このコンポーネントの出力は、イラスト生成と Markdown 生成の両方を駆動する。

---

# Illustration Generator

目的：

教育プランを、一貫した視覚的な説明へと変換する。

イラストジェネレータは、常にプロジェクトのイラストポリシーに従うべきである。

責務には次が含まれる。

* レイアウトの選択
* アスペクト比の選択
* 視覚的な階層の決定
* 視覚的な一貫性の維持

イラストのスタイルを、アプリケーションコードに直接埋め込んではならない。

専用のプロンプトテンプレートに属する。

---

# Markdown Generator

人間が読めるノートを生成する。

各ノートは標準テンプレートに従う。

* フロントマター
* Summary
* Illustration
* Background
* Key Takeaways
* Related Notes
* References
* Tags

Markdown は、長期の知識形式として最も重要である。

---

# Knowledge Linker

Linker は、関係を見つけることで生成済みのノートを充実させる。

例：

* 関連概念
* 前提知識
* 発展的なトピック
* 既存のノート

このコンポーネントは、孤立したノートを、つながった知識グラフへと変える。

---

# 保存レイヤー（Storage Layer）

## Obsidian Vault

Vault は主たる知識リポジトリである。

このコードリポジトリの**外**にあり、`vault_path` で指定される外部の場所に置かれる（ADR 0002）。
保存レイヤーは Knowledge Node をその外部 Vault に書き込む。このコードリポジトリは、知識データ
そのものを決して含まない。

生成された知識はすべて、AI なしでも編集可能なままであるべきである。

フォルダの整理方法は別途定義する。

---

## Git

ここでの Git は、**外部 Vault 自身の任意のバージョン管理**を指す——このコードリポジトリの
Git とは別物である。外部 Vault が Git 管理下にあり `auto_commit` が有効なとき、生成された変更が
そこにコミットされる。

Git が提供するもの：

* 変更履歴
* 再現性
* ロールバック
* 同期

意味のある変更はすべてコミットすべきである。

---

## GitHub

GitHub は次を担う。

* バックアップ
* コラボレーションの場
* プロジェクト管理
* Issue トラッキング

---

# データフロー

すべての実行は、同じライフサイクルに従う。

```
Input

↓

Classification

↓

Knowledge Extraction

↓

Normalization

↓

Educational Planning

↓

Illustration

↓

Markdown

↓

Knowledge Linking

↓

Vault

↓

Git

↓

GitHub
```

---

# リポジトリ構成

```
backend/
    parser/
    planner/
    prompts/
    image/
    markdown/
    linker/
    storage/
    services/
    models/

docs/

tests/

scripts/
```

Obsidian Vault はこの構成の**一部ではない**。外部にあり、`vault_path` で参照される（ADR 0002）。

各ディレクトリは、明確で独立した責務を持つべきである。

---

# AI の役割分担

ChatGPT

* アーキテクチャ
* 教育設計
* イラスト用プロンプト設計

Claude Code

* 実装
* テスト
* リファクタリング
* リポジトリの整備

その他の AI アシスタント

* ベンチマーク
* 実験
* リサーチ

---

# 拡張性

将来のコンポーネント候補：

* RSS の取り込み
* arXiv 連携
* YouTube の取り込み
* ポッドキャストの要約
* セマンティック検索
* ローカル埋め込みの生成
* 知識のレコメンド
* タイムライン可視化

これらは、既存のパイプラインを置き換えるのではなく、拡張する形で統合すべきである。

---

# アーキテクチャ上の制約

アーキテクチャは次を避けるべきである。

* 密結合なコンポーネント
* 重複したビジネスロジック
* 中核モジュールにおける AI 固有の前提
* ハードコードされたプロンプト文
* 実装固有の保存ロジック

コンポーネントは、明確に定義されたデータ構造を通じて通信すべきである。

---

# 長期アーキテクチャビジョン

AI Second Brain は、知識のオペレーティングシステムとして設計されている。

アーキテクチャは、新しい知識ソース・AI モデル・出力形式を、システムを再設計することなく
追加できる、モジュラーなプラットフォームへと進化していくべきである。

究極の目標は、知識が継続的に育ち、つながり、時間とともに理解しやすくなっていくシステムで
ある。
