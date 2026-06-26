# Issue #5: 設定ローダの実装

Labels: core, infrastructure
Milestone: Phase 1 — Foundation

## Why
Vault パス（外部Obsidian）・言語・画像モデル・auto_commit などを安全に読み込み、不正設定を早期に検出する必要がある。

## Goal
`config/settings.toml` を型付き・検証付きで読み込む設定ローダを実装する。

## Tasks
- [ ] pydantic-settings（または同等）で型付き設定モデルを実装
- [ ] 既存項目をサポート：`vault_path`（外部・必須）/ `image_output_dir` / `default_aspect_ratio` / `image_model` / `default_language` / `auto_commit`
- [ ] 新規項目を追加：`image_quality`（low/medium/high。コスト差が大きいため明示設定）
- [ ] `image_model` の既定値を `gpt-image-2` に更新し、`settings.example.toml` も追従
- [ ] `vault_path` の存在・書き込み可否を早期検証し、意味のあるエラーを返す
- [ ] example との差分・必須項目欠落のテスト

## Definition of Done
- 不正・欠落設定で意味のあるエラーが出る
- `settings.example.toml` が最新項目（gpt-image-2 / image_quality）を反映
- 単体テスト通過
