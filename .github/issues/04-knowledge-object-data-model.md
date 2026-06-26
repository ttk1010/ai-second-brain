# Issue #4: Knowledge Object データモデルの実装

Labels: core, data-model
Milestone: Phase 1 — Foundation

## Why
Knowledge Object は全コンポーネントが消費する単一の真実源（DATA_MODEL.md）。これが固まらないと下流（Markdown/Illustration/Metadata/Linker）が実装できない。

## Goal
pydantic で Knowledge Object および関連構造を正式スキーマ化する。

## Tasks
- [ ] `backend/models/` に Knowledge Object スキーマを実装
  - id / source / title / summary / concepts / entities / relationships / educational_plan / references / metadata / outputs
- [ ] Educational Plan スキーマ（learning_objective / target_audience / prerequisites / key_messages / visualization_strategy）を実装。`visualization_strategy` にアスペクト比を持たせる（#1準拠）
- [ ] Metadata スキーマ（source_url / published_date / author / tags / categories / confidence / reading_time / language）
- [ ] Relationship スキーマ（prerequisite / related / successor / alternative / implementation / regulation / application）
- [ ] `outputs` は生成成果物への参照（パス/ID）のみ保持する設計を徹底（プレゼン情報非混入）
- [ ] シリアライズ/デシリアライズ往復テスト、バリデーションテスト

## Definition of Done
- スキーマの単体テストが通る
- プレゼンテーション情報を含まない設計ルールを満たす
- 後続のジェネレータがこのモデルのみを入力に取れる
