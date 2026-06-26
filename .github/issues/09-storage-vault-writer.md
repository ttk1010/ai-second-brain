# Issue #9: Storage層（外部Vault書き込み + Knowledge Node）

Labels: core, storage
Milestone: Phase 1 — Foundation

## Why
生成した知識を、リポジトリ外の Obsidian Vault に Knowledge Node として永続化する必要がある（Vaultは外部＝#2準拠）。

## Goal
Knowledge Object → Knowledge Node を、設定された外部 Vault のフォルダ構成に保存する。

## Tasks
- [ ] `backend/storage/` に Vault Writer を実装
- [ ] 保存先は `vault_path`（外部絶対パス）配下。CHARTER のフォルダ構成（00 Inbox / 01 Concepts / 02 Models / ... / Templates）へ振り分け
- [ ] ファイル名生成規則（衝突回避・冪等性）を定義
- [ ] 画像出力先（`image_output_dir`）への保存と Markdown からの相対参照
- [ ] 一時Vaultディレクトリを使った書き込みテスト（既存ノート衝突の安全処理を含む）

## Definition of Done
- ノートが外部Vaultの正しいフォルダに保存される
- 既存ノートとの衝突を安全に処理する
- ストレージ技術が差し替え可能な抽象（storage層に隔離）になっている
