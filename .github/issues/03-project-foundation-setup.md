# Issue #3: プロジェクト基盤のセットアップ（uv / lint / test / CI）

Labels: infrastructure, tooling
Milestone: Phase 1 — Foundation

## Why
一貫した開発環境とCIがないと、コード品質と長期保守性を担保できない。実装Issueに着手する前に土台を固める。

## Goal
uv ベースの Python プロジェクト雛形、lint/format、テスト基盤、CI を用意する。

## Tasks
- [ ] uv による `pyproject.toml` を作成（Python バージョン固定、依存管理）
- [ ] `ruff`（lint + format）設定を追加
- [ ] `pytest` 雛形と `tests/` 骨格を用意
- [ ] `backend/` の確定レイアウト（#2準拠）に沿った空パッケージ骨格を作成
- [ ] GitHub Actions ワークフローを追加（`ruff check` + `uv run pytest`）
- [ ] 開発手順を README または `docs/` に追記

## Definition of Done
- `uv run pytest` と `ruff check` がローカルおよび CI で成功（緑）
- 新規コントリビュータが手順どおりに環境構築できる
