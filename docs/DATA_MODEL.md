# データモデル

Version: 1.0

Status: Draft

---

# 目的

このドキュメントは、AI Second Brain 全体で使う正本のデータモデルを定義する。

ねらいは、システム内で知識を表現するための唯一の source of truth（正本）を確立すること。

各コンポーネントは、生のテキストをやり取りするのではなく、明確に定義されたデータ構造を
消費・生成すべきである。

---

# 設計思想

AI Second Brain は、2 つの基本概念を区別する。

* **Knowledge Object** — 知識の、内部的で構造化された表現。
* **Knowledge Node** — 知識ベースに保存される永続的な成果物（例：Obsidian のノート）。

この分離により、ビジネスロジック・表示・保存が互いに独立に保たれる。

---

# 知識のライフサイクル

```text
生の入力
    │
    ▼
知識の抽出
    │
    ▼
Knowledge Object
    │
    ▼
教育プランニング
    │
    ├── Markdown
    ├── イラスト
    ├── メタデータ
    └── 関連ノート
    │
    ▼
Knowledge Node
    │
    ▼
Obsidian Vault
```

---

# Knowledge Object

Knowledge Object は、アプリケーション内部における知識の正本の表現である。

イラスト生成・Markdown 生成・メタデータ生成・ノートのリンク付けを含む、下流のすべての
コンポーネントは、同じ Knowledge Object を消費しなければならない。

Knowledge Object は、表示に固有の情報を決して含んではならない。

---

## 概念的な構造

```text
KnowledgeObject
├── id
├── source
├── title
├── short_title
├── summary
├── background
├── key_takeaways
├── concepts
├── entities
├── relationships
├── educational_plan
├── comparison (optional)
├── references
├── metadata
└── outputs (optional)
```

`comparison` は比較ノート（例：「GPT vs Claude vs Gemini」）でのみ設定される。比較対象の
`items`、`rows`（比較の観点1つと、`items` に対応した各項目の短いセル）、`recommendation`
（どの場面でどれを選ぶか）を保持する。Markdown の比較表は、これから決定論的に描画される
（ADR 0007）。比較対象は `concepts` にも追加され、ノートが各項目のノートへリンクするように
なる。

`short_title` は、ノートのファイル名（およびイラストのファイル名）に使う簡潔なラベルである。
説明的な完全版の `title` はフロントマターと見出しに残る。空のときは `title` にフォールバック
する。概念では単に概念名（例：`Neural Network`）、ニュースでは主要なエンティティと中心
トピック（例：`Midjourney、医療ハードウェアに参入`）になる。

`background`（背景と、そのトピックがなぜ重要か）と `key_takeaways`（読者が覚えておくべき
数点）は、要約と一緒に抽出される、読者向けの知識コンテンツである。これらは教育プランの
`key_messages` とは別物である。`key_messages` は、ノートが読者に何を提示するかではなく、
*どう* 教え・図解するかを導くものである。

`outputs` フィールドは **参照のみ** を保持する——生成された成果物（Markdown・イラストなど）を
指すファイルパスや ID である。成果物の中身そのものは決して保存しない。これにより Knowledge
Object を表示データから切り離す（ADR 0001）。

ノートには既定でイラストが 1 枚ある。ユーザーが複数ページシリーズ（`--pages`、ADR 0012）を
選んだ場合、教育プランが `pages` リストを持ち、順序付きのページパスが `illustrations` に
記録される。`outputs['illustration']` は引き続き 1 枚目を指すので、単一ページを前提とする
消費側は影響を受けない。

---

## 責務

Knowledge Object は次を表すべきである。

* そのトピックが何か
* なぜ重要か
* どう動くか
* 既存の知識とどう関係するか

次からは独立しているべきである。

* Markdown の整形
* イラストのレイアウト
* Obsidian の構造
* ファイル名

---

# 教育プラン（Educational Plan）

教育プランは Knowledge Object の一部である。

その責務は、知識を *どう* 教えるかを定義すること。

典型的なフィールド：

* 学習目標
* 対象読者
* 前提知識
* キーメッセージ
* 可視化戦略（選択したアスペクト比を含む）

教育プランは、すべての教育的な出力を駆動する。

イラストの **アスペクト比** は、`visualization_strategy` の一部としてここで決まる。教育
プランナーが（PROJECT_CHARTER.md の「情報の種類 → アスペクト比」対応表を使って）選び、
イラストジェネレータはそれを消費するだけである。教育側が *何を* 見せるかを決め、ジェネレータは
*どう* 描画するかだけを決める（ADR 0001）。

---

# メタデータ

メタデータは、表示ではなく知識そのものを記述する。

例：

* source URL
* 公開日
* 著者
* domain（知識が属する分野。例：「AI」。AI が既定の重点分野 — ADR 0008）
* guidance（ノートを steer した生成時の指示。あれば — Issue #32）
* タグ
* カテゴリ
* 信頼度
* 読了時間
* 言語

メタデータは、すべての出力形式で再利用できるべきである。

---

# 関係（Relationships）

関係は、ある Knowledge Object を他のものとつなぐ。

例：

* prerequisite（前提）
* related concept（関連概念）
* successor（後続）
* alternative（代替）
* implementation（実装）
* regulation（規制）
* application（応用）

関係は論理的なものであり、保存方法からは独立している。

---

# Knowledge Node

Knowledge Node は、Knowledge Object の永続的な表現である。

Second Brain の中に現れる単位である。

現在の実装では、Knowledge Node は次から成る。

* Markdown ノート
* イラスト
* フロントマター
* メタデータ
* バックリンク
* 出典

Knowledge Node は、人間が読むことと、長期の保守に最適化されている。

---

# 知識グラフ

Knowledge Node どうしがつながって知識グラフを形成する。

グラフは、ファイルの階層ではなく概念間の関係を表す。

フォルダ構成は整理の助けになりうるが、主たるナビゲーションのモデルはグラフである。

---

# データの所有権

各コンポーネントには明確な責務がある。

| コンポーネント           | 所有するもの       |
| ------------------------ | ------------------ |
| Extractors               | 生入力の分析       |
| Knowledge Object Builder | Knowledge Object   |
| Educational Planner      | 教育プラン（アスペクト比を含む） |
| Markdown Generator       | Markdown           |
| Illustration Generator   | イラスト           |
| Metadata Generator       | メタデータ         |
| Knowledge Linker         | 関係               |
| Storage Layer            | Knowledge Node     |

どのコンポーネントも、他のコンポーネントの責務を直接書き換えてはならない。

---

# 拡張性

将来の出力形式も、同じ Knowledge Object から生成すべきである。

例：

* HTML
* PDF
* PowerPoint
* Web ページ
* フラッシュカード
* インタラクティブな可視化

どの出力形式も、中核の Knowledge Object の変更を必要とすべきではない。

---

# 設計ルール

* Knowledge Object は唯一の source of truth である。
* すべてのジェネレータは Knowledge Object を消費する。
* Knowledge Node は、明示的に更新されるまで、生成された知識の不変の記録である。
* 表示が Knowledge Object に影響してはならない。
* 保存技術は差し替え可能なままであるべきである。

---

# 長期ビジョン

AI Second Brain が発展するにつれ、Knowledge Object はあらゆる機能の土台になる。

将来の AI モデル・保存バックエンド・出力形式が何であれ、すべての知識は同じ正本の表現を
通るべきである。

**知識**・**表示**・**保存** を分離することで、システムは長年にわたりモジュラーで、
保守しやすく、拡張しやすいままでいられる。
