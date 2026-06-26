# Issue #14: Illustration Storage と Markdown 埋め込み

Labels: core, storage, markdown, image
Milestone: Phase 2 — Educational Content

## Why
生成したイラストを Vault に保存し、ノートから参照できなければ「図解付きノート」が完成しない。現状 Markdown の Illustration セクションは `ILLUSTRATION_PLACEHOLDER` のまま（`backend/markdown/generator.py`）。これを実画像へ置き換え、イラスト系統（#11〜#13）を E2E で完成させる。

## Why（補足：データ方針）
画像は出力（参照）であり、KO には参照のみを記録する（ADR 0001 references only）。画像の実体は外部 Vault に保存し、リポジトリには知識データを持たない（ADR 0002）。

## Goal
生成イラストを Vault の `image_output_dir`（既定 `Images`）に保存し、Markdown の Illustration セクションに相対リンクで埋め込む。

## Tasks
- [ ] `backend/storage/` にイラスト保存処理を追加（`vault_path/image_output_dir` 配下、衝突回避・冪等なファイル名規則）
- [ ] 保存先パスを `ko.outputs['illustration']` に Vault 相対参照で記録
- [ ] `MarkdownGenerator` の Illustration セクションを、参照がある場合は実画像リンク（`![[...]]` または相対パス）で描画、無い場合は従来のプレースホルダ
- [ ] Pipeline に Planner→PromptBuilder→ImageProvider→保存→埋め込みの結線を追加（画像生成失敗時もノート自体は生成できるフォールバック方針を定義）
- [ ] 一時 Vault とモック ImageProvider を使った E2E テスト（外部API非依存）

## Definition of Done
- 概念入力から「要約＋イラスト＋メタデータ」が揃ったノートが生成される（Phase 2 成功基準）
- イラストが Vault に保存され、Markdown から正しく参照される
- 画像生成に失敗してもノート生成は破綻しない（明示的に劣化）
- テストが外部API非依存で通る

## Notes
- これで Phase 2 のイラスト系統が E2E で完成する。
