# Issue #27: Claude Code Channels 連携（チャット投入）

Labels: skill, automation, documentation
Milestone: Phase 4 — Automation

## Why
モバイル/PC からチャットで投入できると日常運用が一気に楽になる。自作サーバを持たず、Claude Code Channels（Telegram）経由で、ローカル起動中の Claude Code が `asb` を実行して Vault に書き込む（ADR 0006）。OpenAI 生成コストは従来どおりで、固定ホスティング費・濫用面はなし。

## Goal
Channels でメッセージ（概念 or URL）を送ると、Claude が `asb` を実行してノート化し結果を返す、という運用を成立させる。リモートから許可プロンプトを承認できない制約に対応する。

## Tasks
- [ ] `.claude/skills/asb-capture/SKILL.md`：受け取ったメッセージ（概念 or URL）を `asb` で処理し、作成/既存/失敗を簡潔に報告する手順
- [ ] `.claude/settings.json`（コミット対象）に `asb` 実行コマンドの事前許可を追加（Channels はリモート承認不可のため）
- [ ] README/docs：Channels + Telegram のセットアップ手順、事前許可、コスト（Pro サブスク内・OpenAI は生成分のみ）、ターミナル常駐が必要な制約を記載
- [ ] 動作確認手順（`asb` は検証済みのため、本 Issue は結線・ドキュメントが中心。実際の Telegram 往復はユーザー環境での設定が前提）

## Definition of Done
- スキルと事前許可が用意され、Channels から `asb` 実行→ノート化の運用が文書化されている
- 既存 CLI を再利用し、追加の常時起動サーバを持たない
- セットアップ手順とコスト・制約がドキュメント化されている

## Notes
- Channels 自体は Telegram/Discord/iMessage 対応。まず Telegram を対象にし、他は同じ仕組みで後から追加可能。
- 実際の Bot 作成・ペアリングはユーザー操作（コードではない）。
