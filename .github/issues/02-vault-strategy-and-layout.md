# Issue #2: Vault戦略とリポジトリ構成の確定

Labels: design, documentation
Milestone: Phase 1 — Foundation

## Why
Vault は「リポジトリ外の Obsidian Vault」を指すと決定した。しかし README.md / CLAUDE.md はリポジトリ構成に `vault/` を含め「Knowledge lives inside the Vault」と記述しており、今回の決定と矛盾する。Vault が外部なら Git追跡の対象範囲（コード/docs のみ）も再定義が必要。`backend/` 内部レイアウトも未確定。

## Goal
Vault配置・Git追跡範囲・`backend/` 内部レイアウトを正式決定し、関連ドキュメントの不整合をまとめて修正する。

## Tasks
- [ ] 「Vault はリポジトリ外の Obsidian Vault を指す」を ADR 化（`docs/adr/0002-vault-and-layout.md`）
- [ ] README.md / CLAUDE.md / ARCHITECTURE.md からリポジトリ内 `vault/` 前提の記述を修正（リポジトリのGit管理対象は backend/docs/scripts/tests のみ）
- [ ] ARCHITECTURE.md の「Vault → Git → GitHub」フローの意味を再定義（コードリポジトリのGitと、Vault側の同期/バージョン管理を区別）
- [ ] `settings.example.toml` の `vault_path`（外部絶対パス）が正であることを確認・明記
- [ ] `backend/` 内部レイアウト（parser/ planner/ prompts/ image/ markdown/ linker/ storage/ services/ models/）を正式採択し、CLAUDE.md のフラット構成に注記を追加
- [ ] 同時に `settings.example.toml` の `image_model` を `gpt-image-2` に更新（旧 `gpt-image-1` 表記の修正）

## Definition of Done
- README/CLAUDE/ARCHITECTURE が「Vaultは外部」で整合
- `docs/adr/0002-vault-and-layout.md` が完成
- `backend/` 内部レイアウトが確定し、後続実装Issueが従える
