# Issue #1: 設計不整合の解消とADR基盤の整備

Labels: design, documentation
Milestone: Phase 1 — Foundation

## Why
ドキュメント整備の過程で設計変更が重なり、ARCHITECTURE.md と DATA_MODEL.md の間で用語・スキーマに不整合がある。実装前に単一の真実源へ揃えないと、コア（Knowledge Object）の手戻りが発生する。

## Goal
設計ドキュメントの矛盾を解消し、確定した設計判断を ADR（Architecture Decision Record）として記録する。

## Tasks
- [ ] `docs/adr/` を新設し、ADRテンプレートを用意する
- [ ] 「Knowledge Normalizer」を「Knowledge Object Builder」に用語統一（ARCHITECTURE.md を DATA_MODEL.md に追従させる）
- [ ] Input Classifier の5分類（Concept/News/Research Paper/Documentation/Unknown）と Extractor の2経路（Concept/News）の不整合を整理。第一版スコープを Concept/News に確定し、Paper/Documentation/Unknown のフォールバック方針を明記
- [ ] Knowledge Object の `outputs` フィールドを「生成済み成果物への参照（パス/ID）のみ保持」と定義し、「プレゼン情報を含まない」設計ルールとの整合を取る
- [ ] アスペクト比の決定責務を「Educational Plan の `visualization_strategy` が保持 → Illustration Generator が消費」と定義し、DATA_MODEL.md の Data Ownership 表に追記
- [ ] ドキュメント優先順位（PROJECT_CHARTER > CLAUDE > README、データ仕様は DATA_MODEL を正本）を ADR に明文化
- [ ] `docs/adr/0001-design-baseline.md` を作成

## Definition of Done
- ドキュメント間に用語・スキーマの矛盾がない
- `docs/adr/0001-design-baseline.md` が main にマージ済み
- 後続Issue（#4 データモデル等）が参照できる確定仕様が存在する
