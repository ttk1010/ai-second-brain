# Issue #10: CLIによるE2E結線（Phase 1 完了）

Labels: core, cli
Milestone: Phase 1 — Foundation

## Why
Phase 1 の Success Criteria「概念/URL を入力すると Vault に Markdown ノートが保存される」を満たす、最初のエンドツーエンド体験を提供する。

## Goal
input → classify → extract → build → markdown → vault →（任意で git commit）を CLI で結線する。

## Tasks
- [ ] `backend/services/` にパイプライン統合（各コンポーネントのオーケストレーション）を実装
- [ ] CLI を実装（概念 or URL を引数に取り、Vaultへ保存）
- [ ] `auto_commit` 設定が true のとき、Vault側の変更を Git コミット（外部Vaultが Git管理下にある場合）
- [ ] 一時Vaultを使った統合テスト（LLM/画像はモック）
- [ ] README に使用例（コマンド例・前提設定）を追記

## Definition of Done
- 概念/URL 入力で Vault に Markdown ノートが保存される
- `auto_commit` 設定に応じて自動コミットされる
- 統合テストが通り、Phase 1 の Success Criteria を満たす

## Notes
- イラスト生成（gpt-image-2）の本接続は Phase 2 で行う。Phase 1 では ImageProvider のモック/プレースホルダで結線する
