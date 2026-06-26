# Issue #12: Illustration Prompt Builder（イラストプロンプト生成）

Labels: core, prompts, image
Milestone: Phase 2 — Educational Content

## Why
イラスト生成は教育資産であり、装飾的グラフィックを作ってはならない（Illustration Principles）。スタイルやレイアウト指示をアプリコードに直書きせず、専用のプロンプトテンプレートに分離する必要がある（ARCHITECTURE「Illustration styles should never be embedded directly in application code」）。

## Goal
Educational Plan（#11）と Knowledge Object から、一貫した教育的イラストを生成するためのプロンプトを構築する。

## Tasks
- [ ] `backend/prompts/illustration/` にイラスト用システム/ユーザープロンプトのテンプレートを追加
- [ ] 一貫した視覚言語（同じ概念は同じ表現）・明瞭さ優先・教育目的のスタイル指示を組み込む
- [ ] Educational Plan の図解対象・視覚階層・aspect ratio をプロンプトに反映
- [ ] `backend/image/` または `backend/prompts/` 配下に Prompt Builder 関数を実装（テンプレート＋KO/Plan → 最終プロンプト文字列）
- [ ] スタイル定義はコードに直書きせずテンプレート側に置く（PROMPT_STYLE_GUIDE 準拠）
- [ ] 決定的なプロンプト生成を検証する単体テスト（LLM/画像API非依存）

## Definition of Done
- KO + Educational Plan から決定的にイラストプロンプトが生成される
- スタイル指示がコードに埋め込まれていない（テンプレートに分離）
- テストが外部API非依存で通る

## Notes
- 実際の画像生成は #13。本 Issue はプロンプト文字列を作るところまで。
