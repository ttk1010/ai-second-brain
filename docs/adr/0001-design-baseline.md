# ADR 0001: Design baseline — terminology, pipeline scope, data ownership

- Status: Accepted
- Date: 2026-06-26
- Deciders: Project owner (ttk1010), Lead Software Engineer (Claude Code)

## Context

ドキュメント整備の過程で設計変更が重なり、`docs/ARCHITECTURE.md` と `docs/DATA_MODEL.md` の間で用語・スキーマ・コンポーネント境界に不整合が生じた。実装（特に Knowledge Object データモデル）に着手する前に、単一の真実源へ揃える必要がある。

本 ADR はデータモデルとコンポーネント境界に関する設計基準を確定する。Vault の配置・Git 追跡範囲・`backend/` 内部レイアウトは別途 ADR 0002（Issue #2）で扱う。

検出した不整合:

1. ARCHITECTURE.md に「Knowledge Normalizer」というコンポーネントがあるが、DATA_MODEL.md では同役割を「Knowledge Object Builder」が担っており、名称が二重。
2. Input Classifier は5分類（Concept / News / Research Paper / Documentation / Unknown）を想定するが、Extractor は2経路（Concept / News）しか定義されていない。
3. Knowledge Object に `outputs (optional)` フィールドがあるが、「Knowledge Object はプレゼン情報を含まない」という設計ルールと矛盾しうる。
4. CHARTER は情報タイプ→アスペクト比の自動選択表を持つが、その決定責務を負うコンポーネントが未定義。
5. ドキュメント優先順位は CLAUDE.md が CHARTER > CLAUDE > README と規定するが、データ仕様の正本がどれかは未明記。

## Decision

### 1. コンポーネント名を Knowledge Object Builder に統一する

「Knowledge Normalizer」という名称を廃止し、入力を正規の内部表現へ変換するコンポーネントを **Knowledge Object Builder** に一本化する。データ仕様は DATA_MODEL.md を正本とし、ARCHITECTURE.md をこれに追従させる。

### 2. Phase 1 の処理経路は Concept / News の2経路に確定する

Input Classifier は5つの分類ラベル（Concept / News / Research Paper / Documentation / Unknown）を出力しうるが、Phase 1 では実処理経路を **Concept パイプライン** と **News パイプライン** の2つに限定し、分類ラベルを次のとおりマップする:

- Concept → Concept パイプライン
- News → News パイプライン
- Research Paper → 当面 News パイプラインで暫定処理（URL 系として扱う）
- Documentation → 当面 News パイプラインで暫定処理（URL 系として扱う）
- Unknown → URL として解釈できれば News パイプラインにフォールバック。概念ともURLとも解釈できない場合は明示的なエラーで停止する（CLAUDE.md「Fail fast」「silently ignore しない」に準拠）

Research Paper / Documentation の専用パイプラインは将来 Issue で追加する。

### 3. `outputs` フィールドは参照のみを保持する

Knowledge Object の `outputs` フィールドは、生成済み成果物への**参照（ファイルパスまたは ID）のみ**を保持する。Markdown 本文・イラストのバイナリ・整形済みプレゼンテーションデータといった実体は保持しない。これにより「Knowledge Object はプレゼン情報を含まない」という設計ルールを維持する。

### 4. アスペクト比は Educational Plan が保持し、Planner が決定する

アスペクト比は Educational Plan の `visualization_strategy` フィールドが保持する。**Educational Planner が決定し、Illustration Generator が消費する**。CHARTER の情報タイプ→アスペクト比表（Process/Workflow=16:9, Hierarchical=4:3, Single Concept=1:1, Step-by-step=9:16）は Planner の判断基準とする。

### 5. データ仕様は DATA_MODEL.md を正本とする

CLAUDE.md のドキュメント優先順位（PROJECT_CHARTER > CLAUDE > README）に加え、**データ構造・スキーマに関しては DATA_MODEL.md を正本**とする。アーキテクチャ図（ARCHITECTURE.md）とデータ仕様（DATA_MODEL.md）が食い違う場合、データ仕様は DATA_MODEL.md が優先する。

## Consequences

- ARCHITECTURE.md / DATA_MODEL.md の用語とコンポーネント境界が一致し、Issue #4（Knowledge Object データモデル）が確定仕様の上に実装できる。
- Phase 1 のスコープが Concept / News に明確化され、Extractor の実装範囲が限定される（Issue #6, #7）。
- `outputs` の定義が固まり、Knowledge Object のプレゼン非依存性が保たれる。
- アスペクト比の決定責務が確定し、Educational Plan スキーマ（Issue #4）と Illustration Generator（Phase 2）の境界が明確になる。
- Research Paper / Documentation を News 経路で暫定処理するため、これらに最適化されていない出力になりうる。専用パイプラインは将来の改善点として残る。

## Alternatives considered

- **5経路を最初から実装する**: スコープが膨らみ Phase 1 の「Minimum Viable Pipeline」原則に反するため不採用。
- **`outputs` フィールドを廃止する**: 生成済み成果物の追跡が別管理になり、Knowledge Node との対応付けが煩雑になるため、参照保持に限定する形で残す。
- **アスペクト比を Illustration Generator が決定する**: 教育的意図（何をどう見せるか）と描画（どう描くか）が混ざり、単一責任原則に反するため不採用。決定は Planner、描画は Generator に分離する。
