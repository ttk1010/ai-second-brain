# Issue #22: Vault索引と安全なRelated Notes更新（決定論コア）

Labels: core, linker
Milestone: Phase 3 — Knowledge Organization

## Why
Phase 3 で知識ノードを繋ぐには、(1) 既存ノートの構造化データを読む手段と、(2) ノートを壊さずに関連リンクを書き込む手段が必要。賢い「どれが関連か」の判断は Claude Code スキル（#23, Pro サブスク内＝OpenAI課金なし）に任せ、本Issueはその土台となる**決定論的で安全な読み書き**を提供する。

## Goal
Vault の全ノートを索引化し、各ノートの「Related Notes」セクションだけを安全・冪等に更新できるライブラリと CLI を用意する。LLM は使わない（追加API課金ゼロ）。

## Tasks
- [ ] `backend/linker/` に `VaultIndex` を実装：Vault走査＋frontmatter解析（title / id / tags / source_type / path）。frontmatter解析のため pyyaml を追加。frontmatter欠落ノートも安全に扱う
- [ ] 「Related Notes」セクションのみを置換する安全な更新関数（他セクション・frontmatterは不変、冪等、リンク重複なし、欠落時は適切な位置に挿入）。任意で関係型（prerequisite/related 等）を併記
- [ ] `asb-link` CLI（新規 console script）に2サブコマンド：
  - `index` … 索引を JSON 出力（Claude がこれを読んで関連性を判断する入力になる）
  - `apply <note>` … 与えられた関連リンクで Related Notes を安全更新
- [ ] 一時Vaultを使った単体テスト（索引化、セクション更新の安全性・冪等性、欠落時挿入）

## Definition of Done
- 既存ノート群を索引化でき、`index` が機械可読な JSON を返す
- `apply` が Related Notes セクションのみを安全・冪等に書き換える（他を壊さない）
- LLM 非依存・外部API非依存でテストが通る

## Notes
- KO永続化は不要（索引は frontmatter から復元できる）方針を裏付ける実装。
- 関連性の「判断」は本Issueの範囲外（#23 の Claude スキルが担う）。
