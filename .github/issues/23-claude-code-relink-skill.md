# Issue #23: Claude Code スキル「貯めたノードを繋ぐ」（Tier 1）

Labels: skill, linker, documentation
Milestone: Phase 3 — Knowledge Organization

## Why
ノート同士の意味的な関連付け（表記揺れや概念的な近さの判断）は LLM が得意。これを OpenAI API で毎回課金するのではなく、**Claude Code のスキルとして実行＝既存の Claude Pro サブスク内で行い、OpenAI 課金をゼロ**にする（Phase 4 Channels と同じ「賢い処理は Claude 側に寄せる」思想）。スキル実行のたびに、それまでに貯まった知識ノードを繋ぐ。

## Goal
オンデマンド実行で Vault 全体を再リンクする Claude Code スキルを用意する。Claude が関連性と関係型を判断し、#22 の安全な CLI で反映する。再実行しても冪等。

## Tasks
- [ ] `.claude/skills/asb-relink/SKILL.md` を作成：手順は (1) `asb-link index` で索引取得 → (2) Claude が関連ノートと関係型を判断 → (3) `asb-link apply` で各ノートの Related Notes を安全更新
- [ ] 既存ノートを壊さない・冪等であることを手順に明記（書き込みは #22 の安全更新経由に限定）
- [ ] 表記揺れ/概念的近さを拾いつつ、無関係なリンクを張りすぎないガイドライン
- [ ] README/docs にスキルの使い方とコスト（Pro サブスク内・OpenAI課金なし）を記載
- [ ] 実Vault または一時Vaultでの動作確認手順（#22 の CLI はテスト済みのため、本Issueは結線確認が中心）

## Definition of Done
- スキル実行で Vault 全体の Related Notes が実在ノートへのリンクに更新される
- 既存ノートの他セクションを壊さない・冪等
- OpenAI API を使わない（追加課金なし）
- 使い方とコストがドキュメント化されている

## Notes
- 判断は Claude、書き込みは #22 の決定論ヘルパー、と役割分担してファイル破損リスクを抑える。
- 逆方向リンク（被リンク）は Obsidian ネイティブ機能に任せる（追加実装不要）。
